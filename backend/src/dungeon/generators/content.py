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
            Dictionary mapping room_id to dimension data
        """
        if not self.is_configured():
            raise ValueError("GROQ API not configured")

        # Create layout description for LLM
        layout_description = self._create_layout_description(layout)

        # Create prompt for room dimensions
        prompt = f"""You are an expert dungeon master. Given this dungeon layout and guidelines, generate appropriate dimensions and basic information for each room.

Dungeon Guidelines:
- Theme: {guidelines.theme}
- Atmosphere: {guidelines.atmosphere}
- Difficulty: {guidelines.difficulty}

Layout Description:
{layout_description}

Generate a JSON response with the following structure for each room:
{{
    "room_id": {{
        "width": <integer 4-12>,
        "height": <integer 3-8>,
        "name": "<descriptive room name>",
        "description": "<brief room description>"
    }}
}}

Focus on:
- Appropriate room sizes for the theme
- Descriptive names that fit the atmosphere
- Brief descriptions that set the scene
- Logical progression through the dungeon

Return only valid JSON:"""

        # Generate response using LLM
        messages = [HumanMessage(content=prompt)]
        response = self.chat_model.invoke(messages)

        try:
            # Parse JSON response using robust parser
            result = _load_json(response.content.strip())

            # Set span attributes for successful generation
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("layout_description", layout_description)
                current_span.set_attribute("response", response.content.strip())
                current_span.set_attribute("is_fallback", False)

            return result
        except json.JSONDecodeError:
            # Fallback to default dimensions
            result = self._generate_fallback_dimensions(layout)

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
        Generate detailed room contents using LLM.

        Args:
            layout: Dungeon layout with dimensions
            guidelines: Generation guidelines
            options: Generation options

        Returns:
            List of RoomContent objects
        """
        if not self.is_configured():
            raise ValueError("GROQ API not configured")

        room_contents = []

        for room in layout.rooms:
            # Create room-specific prompt
            prompt = f"""You are an expert dungeon master. Generate detailed content for this room:

Room: {room.name}
Description: {room.description or 'No description provided'}
Size: {room.width}x{room.height} units
Theme: {guidelines.theme}
Atmosphere: {guidelines.atmosphere}
Difficulty: {guidelines.difficulty}

Generate a JSON response with the following structure:
{{
    "contents": ["item1", "item2", "item3"],
    "atmosphere": "detailed atmospheric description",
    "challenges": ["challenge1", "challenge2"],
    "treasures": ["treasure1", "treasure2"]
}}

Focus on:
- Contents that fit the room's purpose and theme
- Atmospheric details that enhance immersion
- Appropriate challenges for the difficulty level
- Rewarding treasures that make sense for the location

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
                )
                room_contents.append(room_content)

            except json.JSONDecodeError:
                # Fallback to basic content
                room_content = RoomContent(
                    room_id=room.id,
                    name=room.name,
                    description=room.description or "",
                    contents=["basic furniture"],
                    atmosphere="A typical dungeon room",
                    challenges=[],
                    treasures=[],
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
            }

        return result
