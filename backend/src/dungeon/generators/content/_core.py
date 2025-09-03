"""
LLM-based content generation for dungeons.
"""

import os

from langchain_groq import ChatGroq
from opentelemetry import trace

from models.dungeon import (
    DungeonGuidelines,
    DungeonLayout,
    GenerationOptions,
    RoomContent,
)
from src.dungeon.generators.base import BaseContentGenerator
from utils import simple_trace

from ._chain import RoomContentGenerationChain


class LLMContentGenerator(BaseContentGenerator):
    """Generates room content using deterministic sampling for dimensions and LLM for creative content."""

    def __init__(self):
        """Initialize the LLM content generator."""
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.chat_model = None
        self.content_chain = None

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
        Generate detailed content for each room using LLM.

        Args:
            layout: Dungeon layout with rooms (content flags should be pre-sampled by RoomSampler)
            guidelines: Generation guidelines including content percentages
            options: Generation options

        Returns:
            List of RoomContent objects
        """
        if not self.is_configured():
            raise ValueError("LLM is not configured")

        room_contents = []

        for room in layout.rooms:
            # Content flags should already be set on the room object by RoomSampler
            # Just extract them for the prompt
            content_flags = []
            unused_flags = []

            if room.has_traps:
                content_flags.append("traps")
            else:
                unused_flags.append("traps")
            if room.has_treasure:
                content_flags.append("treasure")
            else:
                unused_flags.append("treasure")
            if room.has_monsters:
                content_flags.append("monsters")
            else:
                unused_flags.append("monsters")

            # Use the content chain to generate room content
            chain_inputs = {
                "room": room,
                "layout": layout,
                "guidelines": guidelines,
                "content_flags": content_flags,
                "unused_flags": unused_flags,
            }

            chain_result = self.content_chain.invoke(chain_inputs)
            room_content = chain_result["room_content"]

            room_contents.append(room_content)

            # IMMEDIATELY update the room object in the layout so subsequent rooms can see it
            room.name = room_content.name
            room.description = (
                room_content.player_description
            )  # Use player description for room description

            # Set span attributes for room update
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute(f"room_{room.id}_updated_name", room.name)
                current_span.set_attribute(
                    f"room_{room.id}_updated_description",
                    room.description[:100] if room.description else "",
                )
                current_span.set_attribute(
                    f"room_{room.id}_purpose", room_content.purpose
                )
                current_span.set_attribute(
                    f"room_{room.id}_content_flags_sampled", str(content_flags)
                )
                current_span.set_attribute(
                    f"room_{room.id}_unused_flags_sampled", str(unused_flags)
                )

        return room_contents

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
