"""
LangChain chain for room content generation.
"""

import json
from typing import Any

from langchain.chains.base import Chain
from langchain.schema.messages import HumanMessage

try:
    from opentelemetry import trace
except ImportError:
    trace = None

from models.dungeon import RoomContent
from utils import simple_trace

from ._load_json import _load_json
from ._prompt_builder import RoomContentPromptBuilder


class RoomContentGenerationChain(Chain):
    """
    LangChain chain for generating room content using LLM.

    This chain handles:
    - Building comprehensive prompts with dungeon context
    - Invoking the LLM
    - Parsing and validating responses
    - Error handling with fallback content
    """

    llm: Any
    """The language model to use for content generation."""

    output_key: str = "room_content"
    """The key to use for the output."""

    prompt_builder: RoomContentPromptBuilder
    """The prompt builder for constructing room content prompts."""

    def __init__(self, **kwargs):
        """Initialize the chain with a prompt builder."""
        if "prompt_builder" not in kwargs:
            kwargs["prompt_builder"] = RoomContentPromptBuilder()
        super().__init__(**kwargs)

    @property
    def input_keys(self) -> list[str]:
        """Input keys for the chain."""
        return [
            "room",
            "layout",
            "guidelines",
            "content_flags",
            "unused_flags",
            "allocated_content",
        ]

    @property
    def output_keys(self) -> list[str]:
        """Output keys for the chain."""
        return [self.output_key]

    @simple_trace("RoomContentGenerationChain.generate_room_content")
    def _call(
        self,
        inputs: dict[str, Any],
        run_manager: Any = None,
    ) -> dict[str, Any]:
        """Execute the chain."""
        room = inputs["room"]
        layout = inputs["layout"]
        guidelines = inputs["guidelines"]
        content_flags = inputs["content_flags"]
        unused_flags = inputs["unused_flags"]
        allocated_content = inputs.get("allocated_content", {})

        # Build the prompt using the prompt builder
        prompt = self.prompt_builder.build_prompt(
            room, layout, guidelines, content_flags, unused_flags, allocated_content
        )

        # Generate response using LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        if not response or not response.content:
            raise ValueError("Empty LLM response")

        try:
            # Parse JSON response using robust parser
            content_data = _load_json(response.content.strip())

            # Validate that we got the expected fields
            if not content_data.get("name") or content_data.get("name") == "":
                print(f"WARNING: Room {room.id} missing or empty name field")
            if (
                not content_data.get("description")
                or content_data.get("description") == ""
            ):
                print(f"WARNING: Room {room.id} missing or empty description field")

            room_content = RoomContent(
                room_id=room.id,
                purpose=content_data.get("purpose", "passage"),
                name=content_data.get("name", f"Room {room.id}"),
                gm_description=content_data.get("gm_description", ""),
                player_description=content_data.get("player_description", ""),
                traps=content_data.get("traps", []),
                treasures=content_data.get("treasures", []),
                monsters=content_data.get("monsters", []),
            )

            # Set span attributes for successful content generation
            current_span = trace.get_current_span() if trace else None
            if current_span:
                current_span.set_attribute(f"room_{room.id}_prompt", prompt)
                current_span.set_attribute(
                    f"room_{room.id}_response", response.content.strip()
                )
                current_span.set_attribute(f"room_{room.id}_is_fallback", False)
                current_span.set_attribute(
                    f"room_{room.id}_content_flags",
                    f"traps:{room.has_traps},treasure:{room.has_treasure},monsters:{room.has_monsters}",
                )
                current_span.set_attribute(
                    f"room_{room.id}_content_data", str(content_data)
                )
                current_span.set_attribute(
                    f"room_{room.id}_content_flags_input", str(content_flags)
                )
                current_span.set_attribute(
                    f"room_{room.id}_unused_flags_input", str(unused_flags)
                )

            return {self.output_key: room_content}

        except (json.JSONDecodeError, KeyError, TypeError) as e:
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

            # Set span attributes for fallback content generation
            current_span = trace.get_current_span() if trace else None
            if current_span:
                current_span.set_attribute(f"room_{room.id}_prompt", prompt)
                current_span.set_attribute(
                    f"room_{room.id}_response", "fallback_content_generated"
                )
                current_span.set_attribute(f"room_{room.id}_is_fallback", True)
                current_span.set_attribute(
                    f"room_{room.id}_content_flags",
                    f"traps:{room.has_traps},treasure:{room.has_treasure},monsters:{room.has_monsters}",
                )
                current_span.set_attribute(f"room_{room.id}_error", str(e))
                current_span.set_attribute(
                    f"room_{room.id}_raw_response", response.content.strip()
                )
                current_span.set_attribute(
                    f"room_{room.id}_content_flags_input", str(content_flags)
                )
                current_span.set_attribute(
                    f"room_{room.id}_unused_flags_input", str(unused_flags)
                )

            return {self.output_key: room_content}
