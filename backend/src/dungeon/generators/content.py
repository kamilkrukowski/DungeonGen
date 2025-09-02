"""
LLM-based content generation for dungeons.
"""

import json
import os
import random
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
    """Generates room content using deterministic sampling for dimensions and LLM for creative content."""

    def __init__(self):
        """Initialize the LLM content generator."""
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.chat_model = None

        if self.groq_api_key:
            self.chat_model = ChatGroq(
                groq_api_key=self.groq_api_key,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.7,
            )

    def is_configured(self) -> bool:
        """Check if GROQ API is properly configured."""
        return self.chat_model is not None

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
            layout: Dungeon layout with rooms (should already have content flags set)
            guidelines: Generation guidelines including content percentages
            options: Generation options

        Returns:
            List of RoomContent objects
        """
        if not self.is_configured():
            # If LLM is not configured, return basic content
            print("DEBUG: LLM not configured, using fallback content generation")
            return self._generate_basic_content_fallback(layout, guidelines)

        print(f"DEBUG: LLM configured, using {self.chat_model.model_name}")

        room_contents = []

        for room in layout.rooms:
            # Sample content flags for this room based on guidelines
            has_traps = random.random() < guidelines.percentage_rooms_trapped
            has_treasure = random.random() < guidelines.percentage_rooms_with_treasure
            has_monsters = random.random() < guidelines.percentage_rooms_with_monsters

            # Set the content flags on the room object
            room.has_traps = has_traps
            room.has_treasure = has_treasure
            room.has_monsters = has_monsters

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

            # Build the JSON structure based on content flags
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

            prompt = f"""You are an expert dungeon master creating content for a cohesive dungeon experience.

{dungeon_context}

CURRENT ROOM DETAILS:
Room ID: {room.id}
Size: {room.width}x{room.height} units
Required Content: {content_flags_text}
Banned Content: {banned_content_text}

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
            response = self.chat_model.invoke(messages)
            print(f"DEBUG: LLM response received for room {room.id}")

            if not response or not response.content:
                print(f"ERROR: LLM returned empty response for room {room.id}")
                raise ValueError("Empty LLM response")

            try:
                # Parse JSON response using robust parser
                print(
                    f"DEBUG: LLM response for room {room.id}: {response.content.strip()}"
                )
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
                    has_traps=has_traps,
                    has_treasure=has_treasure,
                    has_monsters=has_monsters,
                )
                room_contents.append(room_content)

                # IMMEDIATELY update the room object in the layout so subsequent rooms can see it
                room.name = room_content.name
                room.description = room_content.description
                print(
                    f"DEBUG: Updated room {room.id} in layout: name='{room.name}', description='{room.description[:50]}...'"
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
                        f"traps:{has_traps},treasure:{has_treasure},monsters:{has_monsters}",
                    )

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # Fallback to basic content based on flags
                print(
                    f"DEBUG: Content generation failed for room {room.id} with error: {e}"
                )
                print(f"DEBUG: Raw response was: {response.content.strip()}")
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
                    name=self._generate_fallback_name(
                        room.id, guidelines, has_traps, has_treasure, has_monsters
                    ),
                    description=self._generate_fallback_description(
                        guidelines, has_traps, has_treasure, has_monsters
                    ),
                    contents=fallback_contents,
                    atmosphere=f"A typical {guidelines.theme.lower()} atmosphere",
                    challenges=fallback_challenges,
                    treasures=fallback_treasures,
                    has_traps=has_traps,
                    has_treasure=has_treasure,
                    has_monsters=has_monsters,
                )
                room_contents.append(room_content)

                # IMMEDIATELY update the room object in the layout for fallback case too
                room.name = room_content.name
                room.description = room_content.description
                print(f"DEBUG: Updated room {room.id} in layout with fallback content")

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
                        f"traps:{has_traps},treasure:{has_treasure},monsters:{has_monsters}",
                    )

        return room_contents

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

        # Theme-specific guidance
        theme_guidance = self._get_theme_guidance(
            guidelines.theme, guidelines.difficulty
        )
        if theme_guidance:
            context_parts.append(f"THEME GUIDANCE:\n{theme_guidance}")

        # Room purpose guidance based on content flags
        room_purpose = self._get_room_purpose_guidance(
            current_room.has_traps, current_room.has_treasure, current_room.has_monsters
        )
        if room_purpose:
            context_parts.append(f"ROOM PURPOSE:\n{room_purpose}")

        return "\n\n".join(context_parts)

    def _get_theme_guidance(self, theme: str, difficulty: str) -> str:
        """Get theme-specific guidance for content generation."""
        theme_lower = theme.lower()

        if "crypt" in theme_lower or "tomb" in theme_lower:
            return f"This is a {difficulty} crypt/tomb. Focus on ancient burial chambers, religious artifacts, and undead themes. Rooms should feel sacred yet dangerous."
        elif "castle" in theme_lower or "fortress" in theme_lower:
            return f"This is a {difficulty} castle/fortress. Emphasize military architecture, noble chambers, and strategic defensive positions. Rooms should feel grand and imposing."
        elif "cave" in theme_lower or "cavern" in theme_lower:
            return f"This is a {difficulty} cave system. Focus on natural formations, underground ecosystems, and geological features. Rooms should feel organic and unpredictable."
        elif "dungeon" in theme_lower or "prison" in theme_lower:
            return f"This is a {difficulty} dungeon/prison. Emphasize confinement, torture devices, and escape attempts. Rooms should feel oppressive and claustrophobic."
        elif "temple" in theme_lower or "sanctuary" in theme_lower:
            return f"This is a {difficulty} temple/sanctuary. Focus on religious symbolism, ceremonial spaces, and divine presence. Rooms should feel reverent and mystical."
        else:
            return f"This is a {difficulty} {theme.lower()} dungeon. Create atmospheric content that fits the theme while maintaining appropriate challenge levels."

    def _get_room_purpose_guidance(
        self, has_traps: bool, has_treasure: bool, has_monsters: bool
    ) -> str:
        """Get guidance about the room's purpose based on content flags."""
        purposes = []

        if has_traps:
            purposes.append("This room serves as a defensive or testing area")
        if has_treasure:
            purposes.append("This room is designed to store or protect valuable items")
        if has_monsters:
            purposes.append("This room functions as a lair or guard post")

        if not purposes:
            purposes.append("This room serves as a passage or common area")

        # Add progression guidance
        if has_traps and has_treasure:
            return f"{'; '.join(purposes)}. It's a high-risk, high-reward area that challenges adventurers before they can claim the treasure."
        elif has_traps and has_monsters:
            return f"{'; '.join(purposes)}. It's a dangerous area that combines environmental hazards with living threats."
        elif has_treasure and has_monsters:
            return f"{'; '.join(purposes)}. The treasure is guarded by creatures, requiring combat or stealth to obtain."
        elif has_traps:
            return (
                f"{'; '.join(purposes)}. It tests the adventurers' awareness and skill."
            )
        elif has_treasure:
            return f"{'; '.join(purposes)}. It rewards successful exploration and may indicate progress through the dungeon."
        elif has_monsters:
            return f"{'; '.join(purposes)}. It presents a combat or stealth challenge."
        else:
            return f"{'; '.join(purposes)}. It provides a moment of respite or serves as a transition between more dangerous areas."

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

    def _generate_fallback_name(
        self,
        room_id: str,
        guidelines: DungeonGuidelines,
        has_traps: bool,
        has_treasure: bool,
        has_monsters: bool,
    ) -> str:
        """Generate a thematic fallback name for a room."""
        theme_lower = guidelines.theme.lower()

        # Generate names based on content and theme
        if has_traps and has_treasure and has_monsters:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Guardian's Crypt"
            elif "castle" in theme_lower or "fortress" in theme_lower:
                return "The Trapped Treasury"
            elif "cave" in theme_lower or "cavern" in theme_lower:
                return "The Monster's Lair"
            else:
                return "The Treacherous Chamber"
        elif has_traps and has_treasure:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Trapped Vault"
            elif "castle" in theme_lower or "fortress" in theme_lower:
                return "The Protected Treasury"
            else:
                return "The Trapped Treasury"
        elif has_traps and has_monsters:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Guardian's Chamber"
            elif "cave" in theme_lower or "cavern" in theme_lower:
                return "The Deadly Cavern"
            else:
                return "The Monster's Den"
        elif has_treasure and has_monsters:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Guarded Vault"
            elif "castle" in theme_lower or "fortress" in theme_lower:
                return "The Protected Chamber"
            else:
                return "The Guarded Treasury"
        elif has_traps:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Trap Chamber"
            elif "cave" in theme_lower or "cavern" in theme_lower:
                return "The Deadly Passage"
            else:
                return "The Trap Room"
        elif has_treasure:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Treasure Vault"
            elif "castle" in theme_lower or "fortress" in theme_lower:
                return "The Treasury"
            else:
                return "The Treasure Room"
        elif has_monsters:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return "The Guardian's Chamber"
            elif "cave" in theme_lower or "cavern" in theme_lower:
                return "The Monster's Lair"
            else:
                return "The Monster's Den"
        else:
            if "crypt" in theme_lower or "tomb" in theme_lower:
                return f"The {guidelines.theme.title()} Chamber"
            elif "castle" in theme_lower or "fortress" in theme_lower:
                return f"The {guidelines.theme.title()} Hall"
            elif "cave" in theme_lower or "cavern" in theme_lower:
                return f"The {guidelines.theme.title()} Cavern"
            else:
                return f"The {guidelines.theme.title()} Room"

    def _generate_fallback_description(
        self,
        guidelines: DungeonGuidelines,
        has_traps: bool,
        has_treasure: bool,
        has_monsters: bool,
    ) -> str:
        """Generate a thematic fallback description for a room."""
        theme_lower = guidelines.theme.lower()
        atmosphere_lower = guidelines.atmosphere.lower()

        # Base description based on theme and atmosphere
        if "crypt" in theme_lower or "tomb" in theme_lower:
            base_desc = f"An ancient {guidelines.theme.lower()} chamber with {atmosphere_lower} atmosphere"
        elif "castle" in theme_lower or "fortress" in theme_lower:
            base_desc = f"A grand {guidelines.theme.lower()} room with {atmosphere_lower} ambiance"
        elif "cave" in theme_lower or "cavern" in theme_lower:
            base_desc = f"A natural {guidelines.theme.lower()} formation with {atmosphere_lower} surroundings"
        else:
            base_desc = f"A typical {guidelines.theme.lower()} room with {atmosphere_lower} mood"

        # Add content-specific details
        content_details = []
        if has_traps:
            content_details.append("hidden dangers")
        if has_treasure:
            content_details.append("valuable rewards")
        if has_monsters:
            content_details.append("hostile inhabitants")

        if content_details:
            return f"{base_desc}. This area contains {', '.join(content_details)}."
        else:
            return f"{base_desc}. This area serves as a passage or common space."

    def _generate_basic_content_fallback(
        self, layout: DungeonLayout, guidelines: DungeonGuidelines
    ) -> list[RoomContent]:
        """Generate basic content when LLM is not available."""
        room_contents = []

        for room in layout.rooms:
            # Use the content flags that were already determined during dimension generation
            has_traps = room.has_traps
            has_treasure = room.has_treasure
            has_monsters = room.has_monsters

            # Generate basic content based on flags
            contents = ["basic furniture"]
            challenges = []
            treasures = []

            if has_traps:
                contents.append("suspicious pressure plate")
                challenges.append("hidden trap")
            if has_treasure:
                treasures.append("small chest")
            if has_monsters:
                contents.append("monster lair")
                challenges.append("hostile creature")

            # Generate basic names based on content
            if has_traps and has_treasure and has_monsters:
                name = "Treasure Chamber"
            elif has_traps and has_treasure:
                name = "Trapped Treasury"
            elif has_traps and has_monsters:
                name = "Monster Lair"
            elif has_treasure and has_monsters:
                name = "Guarded Vault"
            elif has_traps:
                name = "Trap Room"
            elif has_treasure:
                name = "Treasure Room"
            elif has_monsters:
                name = "Monster Den"
            else:
                name = f"Chamber {room.id}"

            room_content = RoomContent(
                room_id=room.id,
                name=name,
                description=f"A {guidelines.theme.lower()} room",
                contents=contents,
                atmosphere=f"A typical {guidelines.theme.lower()} atmosphere",
                challenges=challenges,
                treasures=treasures,
                has_traps=has_traps,
                has_treasure=has_treasure,
                has_monsters=has_monsters,
            )
            room_contents.append(room_content)

        return room_contents
