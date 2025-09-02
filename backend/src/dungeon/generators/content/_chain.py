"""
LangChain chain for room content generation.
"""

import json
from typing import Any

from langchain.chains.base import Chain
from langchain.schema.messages import HumanMessage
from opentelemetry import trace

from models.dungeon import DungeonGuidelines, DungeonLayout, RoomContent

from ._load_json import _load_json


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

    @property
    def input_keys(self) -> list[str]:
        """Input keys for the chain."""
        return ["room", "layout", "guidelines", "content_flags", "unused_flags"]

    @property
    def output_keys(self) -> list[str]:
        """Output keys for the chain."""
        return [self.output_key]

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

        # Build the JSON structure based on content flags
        has_treasure = room.has_treasure
        if has_treasure:
            json_structure = """{
    "name": "<descriptive room name that reflects its content and theme>",
    "description": "<brief room description that sets the scene and hints at content>",
    "contents": ["item1", "item2", "item3"],
    "atmosphere": "detailed atmospheric description",
    "challenges": ["challenge1", "challenge2"],
    "treasures": ["treasure1", "treasure2"]
}"""
        else:
            json_structure = """{
    "name": "<descriptive room name that reflects its content and theme>",
    "description": "<brief room description that sets the scene and hints at content>",
    "contents": ["item1", "item2", "item3"],
    "atmosphere": "detailed atmospheric description",
    "challenges": ["challenge1", "challenge2"]
}"""

        # Build comprehensive dungeon context
        dungeon_context = self._build_dungeon_context(layout, guidelines, room)
        print(f"DEBUG: Built dungeon context for room {room.id}: {dungeon_context}")

        content_flags_text = (
            ", ".join(content_flags) if content_flags else "no special content"
        )
        unused_flags_text = (
            ", ".join(unused_flags) if unused_flags else "no banned content"
        )

        prompt = f"""You are an expert dungeon master creating content for a cohesive dungeon experience.

{dungeon_context}

CURRENT ROOM DETAILS:
Room ID: {room.id}
Size: {room.width}x{room.height} units
Required Content: {content_flags_text}
Banned Content: {unused_flags_text}

Generate a JSON response with this exact structure:
{json_structure}

IMPORTANT REQUIREMENTS:
1. The "name" field must be a creative, thematic room name that fits the overall dungeon theme
2. The "description" field must vividly set the scene and hint at the room's purpose
3. All content must be consistent with the dungeon's theme, atmosphere, and difficulty
4. Room names and descriptions should reflect the progression and purpose within the dungeon
5. Only include the required content types specified above
6. Return ONLY valid JSON, no other text
7. Follow any custom instructions provided by the user above
8. Build upon the previously generated rooms to create narrative continuity and progression

CRITICAL: The "name" field must be creative (NOT "Room {room.id}" or generic names).
Return ONLY valid JSON.

NARRATIVE CONTINUITY TIPS:
- Reference elements from previous rooms when appropriate (e.g., "continuing the ancient script from the previous chamber")
- Build upon the established atmosphere and themes
- Create logical progression that makes sense with what came before
- Use the previous rooms' content flags to understand the dungeon's challenge curve"""

        # Generate response using LLM
        print(f"DEBUG: Sending prompt to LLM for room {room.id}")
        print(f"DEBUG: Prompt: {prompt}")
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        print(f"DEBUG: LLM response received for room {room.id}")

        if not response or not response.content:
            print(f"ERROR: LLM returned empty response for room {room.id}")
            raise ValueError("Empty LLM response")

        try:
            # Parse JSON response using robust parser
            print(f"DEBUG: LLM response for room {room.id}: {response.content.strip()}")
            content_data = _load_json(response.content.strip())
            print(f"DEBUG: Parsed content data for room {room.id}: {content_data}")

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
                name=content_data.get("name", f"Room {room.id}"),
                description=content_data.get("description", ""),
                contents=content_data.get("contents", []),
                atmosphere=content_data.get("atmosphere", ""),
                challenges=content_data.get("challenges", []),
                treasures=content_data.get("treasures", []),
                has_traps=room.has_traps,
                has_treasure=room.has_treasure,
                has_monsters=room.has_monsters,
            )

            # Set span attributes for successful content generation
            current_span = trace.get_current_span()
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

            return {self.output_key: room_content}

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Fallback to basic content based on flags
            print(
                f"DEBUG: Content generation failed for room {room.id} with error: {e}"
            )
            print(f"DEBUG: Raw response was: {response.content.strip()}")
            fallback_contents = ["basic furniture"]
            fallback_challenges = []
            fallback_treasures = []

            if room.has_traps:
                fallback_contents.append("suspicious pressure plate")
                fallback_challenges.append("hidden trap")
            if room.has_treasure:
                fallback_treasures.append("small chest")
            if room.has_monsters:
                fallback_contents.append("monster lair")
                fallback_challenges.append("hostile creature")

            room_content = RoomContent(
                room_id=room.id,
                name="ERROR",
                description="ERROR",
                contents=fallback_contents,
                atmosphere="ERROR",
                challenges=fallback_challenges,
                treasures=fallback_treasures,
                has_traps=room.has_traps,
                has_treasure=room.has_treasure,
                has_monsters=room.has_monsters,
            )

            # Set span attributes for fallback content generation
            current_span = trace.get_current_span()
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

            return {self.output_key: room_content}

    def _build_dungeon_context(
        self, layout: DungeonLayout, guidelines: DungeonGuidelines, current_room: Any
    ) -> str:
        """Build comprehensive dungeon context for LLM prompts."""
        context_parts = []

        # Overall dungeon guidelines
        context_parts.append(
            f"""DUNGEON OVERVIEW:
Theme: {guidelines.theme}
Atmosphere: {guidelines.atmosphere}
Difficulty: {guidelines.difficulty}
Overall Style: {guidelines.theme.lower()} dungeon with {guidelines.atmosphere.lower()} atmosphere"""
        )

        # User's custom prompt (if provided)
        if guidelines.prompt and guidelines.prompt.strip():
            print(f"DEBUG: Using custom user prompt: {guidelines.prompt.strip()}")
            context_parts.append(
                f"""USER'S CUSTOM INSTRUCTIONS:
{guidelines.prompt.strip()}"""
            )
        else:
            print("DEBUG: No custom user prompt provided")

        # Room count and layout context
        context_parts.append(
            f"""LAYOUT CONTEXT:
Total Rooms: {len(layout.rooms)}
Current Room: {current_room.id} of {len(layout.rooms)}
Room Size: {current_room.width}x{current_room.height} units"""
        )

        # Room position context (if available)
        if hasattr(current_room, "anchor") and current_room.anchor:
            context_parts.append(
                f"Room Position: ({current_room.anchor.x}, {current_room.anchor.y})"
            )

        # Content distribution context
        total_rooms = len(layout.rooms)
        rooms_with_traps = sum(1 for room in layout.rooms if room.has_traps)
        rooms_with_treasure = sum(1 for room in layout.rooms if room.has_treasure)
        rooms_with_monsters = sum(1 for room in layout.rooms if room.has_monsters)

        context_parts.append(
            f"""CONTENT DISTRIBUTION:
- {rooms_with_traps}/{total_rooms} rooms contain traps
- {rooms_with_monsters}/{total_rooms} rooms contain monsters
- {rooms_with_treasure}/{total_rooms} rooms contain treasure"""
        )

        # Room progression context (if we have connections)
        if layout.connections:
            context_parts.append("ROOM CONNECTIONS:")
            for connection in layout.connections[:5]:  # Limit to first 5 connections
                context_parts.append(
                    f"- {connection.room_a_id} connects to {connection.room_b_id} via {connection.connection_type}"
                )
            if len(layout.connections) > 5:
                context_parts.append(
                    f"... and {len(layout.connections) - 5} more connections"
                )

        # Previously generated rooms context
        previous_rooms = self._get_previous_rooms_context(layout, current_room.id)
        if previous_rooms:
            context_parts.append(f"PREVIOUSLY GENERATED ROOMS:\n{previous_rooms}")

        return "\n\n".join(context_parts)

    def _get_previous_rooms_context(
        self, layout: DungeonLayout, current_room_id: str
    ) -> str:
        """Get context about previously generated rooms for narrative continuity."""
        # Find rooms that come before the current room in the generation order
        # We'll use room ID order as a proxy for generation order
        current_room_index = None
        for i, room in enumerate(layout.rooms):
            if room.id == current_room_id:
                current_room_index = i
                break

        if current_room_index is None or current_room_index == 0:
            return ""  # First room or room not found

        previous_rooms = layout.rooms[:current_room_index]
        if not previous_rooms:
            return ""

        context_lines = []
        for room in previous_rooms:
            # Get room name and description from metadata if available
            room_name = (
                room.name if room.name and room.name.strip() else f"Room {room.id}"
            )
            room_description = (
                room.description
                if room.description and room.description.strip()
                else "No description available"
            )

            # Get content flags for context
            content_flags = []
            if room.has_traps:
                content_flags.append("traps")
            if room.has_treasure:
                content_flags.append("treasure")
            if room.has_monsters:
                content_flags.append("monsters")

            content_summary = (
                f"({', '.join(content_flags)})"
                if content_flags
                else "(no special content)"
            )

            context_lines.append(f"- {room_name} {content_summary}: {room_description}")

        return "\n".join(context_lines)
