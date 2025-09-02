"""
LLM-based content generation for dungeons.
"""

import json
import os
import re
from typing import Any

from langchain.schema import HumanMessage
from langchain_groq import ChatGroq
from opentelemetry import trace

from models.dungeon import (
    DungeonGuidelines,
    DungeonLayout,
    GenerationOptions,
    RoomContent,
)
from utils import simple_trace

from .base import BaseContentGenerator


def _load_json(text: str) -> dict[str, Any]:
    """
    Robust JSON loading that handles various LLM response formats.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed
    """
    # First, try direct JSON parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to extract JSON from backticks
    backtick_pattern = r"`(\{.*?\})`"
    match = re.search(backtick_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in the text
    json_pattern = r"\{.*\}"
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0).strip())
        except json.JSONDecodeError:
            pass

    # Final fallback: use json-repair
    try:
        from json_repair import repair_json

        repaired_json = repair_json(text)
        return json.loads(repaired_json)
    except (ImportError, json.JSONDecodeError) as err:
        raise json.JSONDecodeError(
            f"Could not parse JSON from text: {text[:200]}..."
        ) from err


class LLMContentGenerator(BaseContentGenerator):
    """Generates room content using LLM via GROQ API."""

    def __init__(self):
        """Initialize the LLM content generator."""
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.chat_model = None

        if self.groq_api_key:
            self.chat_model = ChatGroq(
                groq_api_key=self.groq_api_key,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
            )

    def is_configured(self) -> bool:
        """Check if GROQ API is properly configured."""
        return self.chat_model is not None

    @simple_trace("LLMContentGenerator.generate_room_dimensions")
    def generate_room_dimensions(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> dict[str, dict[str, Any]]:
        """
        Generate room dimensions and basic information using LLM.

        Args:
            layout: Basic dungeon layout
            guidelines: Generation guidelines
            options: Generation options

        Returns:
            Dictionary mapping room_id to dimension data including content flags
        """
        if not self.is_configured():
            raise ValueError("GROQ API not configured")

        import random

        # Sample content flags for each room early, so they can inform descriptions
        room_content_flags = {}
        for room in layout.rooms:
            has_traps = random.random() < guidelines.percentage_rooms_trapped
            has_treasure = random.random() < guidelines.percentage_rooms_with_treasure
            has_monsters = random.random() < guidelines.percentage_rooms_with_monsters

            room_content_flags[room.id] = {
                "has_traps": has_traps,
                "has_treasure": has_treasure,
                "has_monsters": has_monsters,
            }

        # Create layout description for LLM
        layout_description = self._create_layout_description(layout)

        # Create prompt for room dimensions with content flags
        prompt = f"""You are an expert dungeon master. Given this dungeon layout and guidelines, generate appropriate dimensions and basic information for each room.

Dungeon Guidelines:
- Theme: {guidelines.theme}
- Atmosphere: {guidelines.atmosphere}
- Difficulty: {guidelines.difficulty}

Layout Description:
{layout_description}

Room Content Flags:
{chr(10).join([f"- {room.name} (ID: {room.id}): {', '.join([k for k, v in room_content_flags[room.id].items() if v]) or 'no special content'}" for room in layout.rooms])}

Generate a JSON response with the following structure for each room:
{{
    "room_id": {{
        "width": <integer 4-12>,
        "height": <integer 3-8>,
        "name": "<descriptive room name that reflects its content>",
        "description": "<brief room description that hints at content>"
    }}
}}

Focus on:
- Appropriate room sizes for the theme
- Descriptive names that fit the atmosphere AND reflect the room's content
- Brief descriptions that set the scene AND hint at what content to expect
- Logical progression through the dungeon
- Room names and descriptions should reflect whether they contain traps, treasure, or monsters

Return only valid JSON:"""

        # Generate response using LLM
        messages = [HumanMessage(content=prompt)]
        response = self.chat_model.invoke(messages)

        try:
            # Parse JSON response using robust parser
            result = _load_json(response.content.strip())

            # Add content flags to the result
            for room_id, room_data in result.items():
                if room_id in room_content_flags:
                    room_data.update(room_content_flags[room_id])
                    print(
                        f"DEBUG: Room {room_id} content flags: {room_content_flags[room_id]}"
                    )

            # Set span attributes for successful generation
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("layout_description", layout_description)
                current_span.set_attribute("response", response.content.strip())
                current_span.set_attribute("is_fallback", False)

            return result
        except json.JSONDecodeError:
            # Fallback to default dimensions with content flags
            result = self._generate_fallback_dimensions(layout)

            # Add content flags to fallback results
            for room_id, room_data in result.items():
                if room_id in room_content_flags:
                    room_data.update(room_content_flags[room_id])
                    print(
                        f"DEBUG: Fallback room {room_id} content flags: {room_content_flags[room_id]}"
                    )

            # Set span attributes for fallback
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("layout_description", layout_description)
                current_span.set_attribute("response", response.content.strip())
                current_span.set_attribute("result", str(result))
                current_span.set_attribute("is_fallback", True)

            return result

    def generate_room_contents(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> list[RoomContent]:
        """
        Generate detailed content for each room using LLM.

        Args:
            layout: Dungeon layout with rooms (should already have content flags set)
            guidelines: Generation guidelines including content percentages
            options: Generation options

        Returns:
            List of RoomContent objects
        """
        if not self.is_configured():
            raise ValueError("GROQ API not configured")

        room_contents = []

        for room in layout.rooms:
            # Use the content flags that were already determined during dimension generation
            has_traps = room.has_traps
            has_treasure = room.has_treasure
            has_monsters = room.has_monsters

            print(
                f"DEBUG: Content generation for room {room.id}: has_traps={has_traps}, has_treasure={has_treasure}, has_monsters={has_monsters}"
            )

            # Create room-specific prompt with content flags
            content_flags = []
            banned_content = []
            if has_traps:
                content_flags.append("traps")
            else:
                banned_content.append("traps")
            if has_treasure:
                content_flags.append("treasure")
            else:
                banned_content.append("treasure")
            if has_monsters:
                content_flags.append("monsters")
            else:
                banned_content.append("monsters")

            content_flags_text = (
                ", ".join(content_flags) if content_flags else "no special content"
            )
            banned_content_text = (
                ", ".join(banned_content) if banned_content else "no banned content"
            )

            # Build the JSON structure dynamically based on content flags
            json_structure = """{
    "contents": ["item1", "item2", "item3"],
    "atmosphere": "detailed atmospheric description",
    "challenges": ["challenge1", "challenge2"]"""

            if has_treasure:
                json_structure += ',\n    "treasures": ["treasure1", "treasure2"]'

            json_structure += "\n}"

            prompt = f"""You are an expert dungeon master. Generate detailed content for this room:

Room: {room.name}
Description: {room.description or 'No description provided'}
Size: {room.width}x{room.height} units
Theme: {guidelines.theme}
Atmosphere: {guidelines.atmosphere}
Difficulty: {guidelines.difficulty}
Required Content: {content_flags_text}
Banned Content: {banned_content_text}

Generate a JSON response with the following structure:
{json_structure}

Focus on:
- Contents that fit the room's purpose and theme
- Atmospheric details that enhance immersion
- Appropriate challenges for the difficulty level
- Rewarding treasures that make sense for the location
- ONLY include the required content types specified above. e.g. exclude monsters or traps or treasure if not required.

Return only valid JSON:"""

            # Generate response using LLM
            messages = [HumanMessage(content=prompt)]
            response = self.chat_model.invoke(messages)

            try:
                # Parse JSON response using robust parser
                content_data = _load_json(response.content.strip())

                room_content = RoomContent(
                    room_id=room.id,
                    name=room.name,
                    description=room.description or "",
                    contents=content_data.get("contents", []),
                    atmosphere=content_data.get("atmosphere", ""),
                    challenges=content_data.get("challenges", []),
                    treasures=content_data.get("treasures", []),
                    has_traps=has_traps,
                    has_treasure=has_treasure,
                    has_monsters=has_monsters,
                )
                room_contents.append(room_content)

            except json.JSONDecodeError:
                # Fallback to basic content based on flags
                fallback_contents = ["basic furniture"]
                fallback_challenges = []
                fallback_treasures = []

                if has_traps:
                    fallback_contents.append("suspicious pressure plate")
                    fallback_challenges.append("hidden trap")
                if has_treasure:
                    fallback_treasures.append("small chest")
                if has_monsters:
                    fallback_contents.append("monster lair")
                    fallback_challenges.append("hostile creature")

                room_content = RoomContent(
                    room_id=room.id,
                    name=room.name,
                    description=room.description or "",
                    contents=fallback_contents,
                    atmosphere="A typical dungeon room",
                    challenges=fallback_challenges,
                    treasures=fallback_treasures,
                    has_traps=has_traps,
                    has_treasure=has_treasure,
                    has_monsters=has_monsters,
                )
                room_contents.append(room_content)

        return room_contents

    def _create_layout_description(self, layout: DungeonLayout) -> str:
        """Create a natural language description of the dungeon layout."""
        description = f"Dungeon with {len(layout.rooms)} rooms:\n"

        for room in layout.rooms:
            description += f"- {room.name} (ID: {room.id})\n"

        description += "\nConnections:\n"
        for connection in layout.connections:
            description += f"- {connection.room_a_id} to {connection.room_b_id} ({connection.connection_type})\n"

        return description

    def _generate_fallback_dimensions(
        self, layout: DungeonLayout
    ) -> dict[str, dict[str, Any]]:
        """Generate fallback dimensions when LLM fails."""
        result = {}

        for room in layout.rooms:
            result[room.id] = {
                "width": 6,
                "height": 4,
                "name": room.name,
                "description": f"A {room.name.lower()}",
                "has_traps": False,
                "has_treasure": False,
                "has_monsters": False,
            }

        return result
