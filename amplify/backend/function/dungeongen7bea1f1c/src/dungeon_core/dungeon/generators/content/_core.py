"""
LLM-based content generation for dungeons.
"""

import os
from typing import Any

from langchain_groq import ChatGroq

try:
    from opentelemetry import trace
except ImportError:
    trace = None

from dungeon_core.dungeon.generators.base import BaseContentGenerator
from models.dungeon import (
    DungeonGuidelines,
    DungeonLayout,
    GenerationOptions,
    RoomContent,
)
from utils import simple_trace

from ._allocator import ContentAllocator
from ._global_planner import GlobalPlanner
from ._per_room import RoomContentGenerationChain


class LLMContentGenerator(BaseContentGenerator):
    """Generates room content using global planning and LLM for creative content."""

    def __init__(self):
        """Initialize the LLM content generator."""
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        if self.groq_api_key:
            # Strip newlines and whitespace from API key to prevent httpx header errors
            self.groq_api_key = self.groq_api_key.strip()

        self.chat_model = None
        self.content_chain = None
        self.global_planner = GlobalPlanner()
        self.content_allocator = ContentAllocator()

        if self.groq_api_key:
            self.chat_model = ChatGroq(
                groq_api_key=self.groq_api_key,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.7,
            )
            self.content_chain = RoomContentGenerationChain(llm=self.chat_model)

    def is_configured(self) -> bool:
        """Check if GROQ API is properly configured."""
        return self.chat_model is not None and self.content_chain is not None

    @simple_trace("LLMContentGenerator.generate_room_contents")
    def generate_room_contents(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> list[RoomContent]:
        """
        Generate detailed content for each room using global planning and LLM.

        Args:
            layout: Dungeon layout with rooms (content flags should be pre-sampled by RoomSampler)
            guidelines: Generation guidelines including content percentages
            options: Generation options

        Returns:
            List of RoomContent objects
        """
        if not self.is_configured():
            raise ValueError("LLM is not configured")

        # STAGE 1: Global Planning
        # Generate treasure lists, monster encounters, and trap themes
        content_plan = self.global_planner.plan_dungeon_content(
            layout, guidelines, options
        )

        # Set the generated dungeon name in the layout
        layout.name = content_plan.name
        print(f"DEBUG: Set dungeon name to: '{content_plan.name}'")

        # Add span attributes for global planning results
        current_span = trace.get_current_span() if trace else None
        if current_span:
            current_span.set_attribute(
                "content_generation.dungeon_name", content_plan.name
            )
            current_span.set_attribute(
                "content_generation.treasure_count", len(content_plan.treasures)
            )
            current_span.set_attribute(
                "content_generation.monster_count", len(content_plan.monsters)
            )
            current_span.set_attribute(
                "content_generation.trap_count", len(content_plan.traps)
            )
            current_span.set_attribute(
                "content_generation.total_value", content_plan.total_value
            )

        # STAGE 2: Content Allocation
        # Distribute the globally planned content to individual rooms
        room_allocations = self.content_allocator.allocate_content(layout, content_plan)

        # Validate the allocation
        allocation_validation = self.content_allocator.validate_allocation(
            layout, content_plan, room_allocations
        )

        if not allocation_validation["is_valid"]:
            print(
                f"WARNING: Content allocation validation failed: {allocation_validation['errors']}"
            )

        # Add span attributes for allocation validation
        current_span = trace.get_current_span() if trace else None
        if current_span:
            current_span.set_attribute(
                "content_generation.allocation_valid", allocation_validation["is_valid"]
            )
            current_span.set_attribute(
                "content_generation.allocation_warnings",
                str(allocation_validation.get("warnings", [])),
            )
            current_span.set_attribute(
                "content_generation.allocation_errors",
                str(allocation_validation.get("errors", [])),
            )
            current_span.set_attribute(
                "content_generation.allocation_stats",
                str(allocation_validation.get("allocation_stats", {})),
            )

        # STAGE 3: Per-Room Content Generation
        # Generate detailed content for each room using the allocated resources
        room_contents = []

        for room in layout.rooms:
            room_content = self._generate_room_content_with_allocated_resources(
                room, layout, guidelines, room_allocations.get(room.id, {})
            )
            room_contents.append(room_content)

            # IMMEDIATELY update the room object in the layout so subsequent rooms can see it
            room.name = room_content.name
            room.description = room_content.player_description

            # Set span attributes for room update
            current_span = trace.get_current_span() if trace else None
            if current_span:
                current_span.set_attribute(f"room_{room.id}_updated_name", room.name)
                current_span.set_attribute(
                    f"room_{room.id}_updated_description",
                    room.description[:100] if room.description else "",
                )
                current_span.set_attribute(
                    f"room_{room.id}_purpose", room_content.purpose
                )

        return room_contents

    def _generate_room_content_with_allocated_resources(
        self,
        room: Any,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        allocated_content: dict,
    ) -> RoomContent:
        """Generate content for a single room using allocated resources."""
        # Extract content flags from allocated content
        content_flags = []
        unused_flags = []

        if allocated_content.get("treasures"):
            content_flags.append("treasure")
        else:
            unused_flags.append("treasure")

        if allocated_content.get("monsters"):
            content_flags.append("monsters")
        else:
            unused_flags.append("monsters")

        if allocated_content.get("traps"):
            content_flags.append("traps")
        else:
            unused_flags.append("traps")

        # Use the content chain to generate room content
        chain_inputs = {
            "room": room,
            "layout": layout,
            "guidelines": guidelines,
            "content_flags": content_flags,
            "unused_flags": unused_flags,
            "allocated_content": allocated_content,  # Pass allocated content for context
        }

        chain_result = self.content_chain.invoke(chain_inputs)
        room_content = chain_result["room_content"]

        # Enhance the room content with allocated resource details
        room_content = self._enhance_with_allocated_content(
            room_content, allocated_content
        )

        return room_content

    def _enhance_with_allocated_content(
        self, room_content: RoomContent, allocated_content: dict
    ) -> RoomContent:
        """Enhance room content with details from allocated resources."""
        # This method can be used to add specific details from the allocated content
        # For now, we'll just return the room content as-is
        # In the future, this could be used to:
        # - Add specific treasure names/descriptions
        # - Include monster stats from the global plan
        # - Add trap DCs and damage from the global plan

        return room_content

    def _generate_basic_content_fallback(
        self, layout: DungeonLayout, guidelines: DungeonGuidelines
    ) -> list[RoomContent]:
        """Generate basic content when LLM is not available."""
        room_contents = []

        for room in layout.rooms:
            room_content = RoomContent(
                room_id=room.id,
                purpose="passage",
                name="ERROR",
                gm_description="ERROR",
                player_description="ERROR",
                traps=[],
                treasures=[],
                monsters=[],
            )
            room_contents.append(room_content)

        return room_contents
