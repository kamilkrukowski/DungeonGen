"""
Prompt builder for room content generation.
"""

from typing import Any

from models.dungeon import DungeonGuidelines, DungeonLayout


class RoomContentPromptBuilder:
    """Builds comprehensive prompts for room content generation."""

    def build_prompt(
        self,
        room: Any,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        content_flags: list[str],
        unused_flags: list[str],
        allocated_content: dict = None,
    ) -> str:
        """Build the complete prompt for room content generation."""
        # Build the JSON structure based on content flags
        json_structure = self._build_json_structure(
            room.has_treasure, room.has_traps, room.has_monsters
        )

        # Build comprehensive dungeon context
        dungeon_context = self._build_dungeon_context(layout, guidelines, room)

        # Build allocated content context if available
        allocated_content_context = ""
        if allocated_content:
            allocated_content_context = self._build_allocated_content_context(
                allocated_content
            )

        # Format content flags text
        content_flags_text = (
            ", ".join(content_flags) if content_flags else "no special content"
        )
        unused_flags_text = (
            ", ".join(unused_flags) if unused_flags else "no banned content"
        )

        return f"""You are an expert dungeon master creating content for a cohesive dungeon experience.

{dungeon_context}

{allocated_content_context}

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

    def _build_json_structure(
        self, has_treasure: bool, has_traps: bool, has_monsters: bool
    ) -> str:
        """Build the JSON structure template based on content flags."""
        _start, _end = "{\n", "\n}"
        core_json = """"purpose": "<purpose of the room, what the owner of the dungeon used it for>",
    "name": "<descriptive room name that reflects its content and theme>",
    "gm_description": "<brief room description for game masters that sets the scene and hints at content>",
    "player_description": "<brief room description to be read aloud to players that sets the scene and hints at content>"""

        conditional_json = ""
        if has_traps:
            conditional_json += """,
    "traps": [
        {
            "name": "<trap name>",
            "trigger": "<what activates the trap>",
            "effect": "<damage/effect details>",
            "difficulty": "<DC and skill requirements>",
            "location": "<where the trap is located>"
        }
    ]"""

        if has_treasure:
            conditional_json += """,
    "treasures": [
        {
            "name": "<treasure name>",
            "description": "<detailed description>",
            "value": "<monetary or intrinsic value>",
            "location": "<where it's hidden/found>",
            "requirements": "<how to access/obtain it>"
        }
    ]"""

        if has_monsters:
            conditional_json += """,
    "monsters": [
        {
            "name": "<monster name>",
            "description": "<physical description>",
            "stats": "<HP, AC, attack bonus, damage>",
            "behavior": "<how it acts>",
            "location": "<where in the room>"
        }
    ]"""

        out = _start + core_json + conditional_json + _end
        return out

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
            context_parts.append(
                f"""USER'S CUSTOM INSTRUCTIONS:
{guidelines.prompt.strip()}"""
            )

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

            # Check if room has a description (from content generation)
            room_description = "No description available"
            if (
                hasattr(room, "gm_description")
                and room.gm_description
                and room.gm_description.strip()
            ):
                room_description = room.gm_description
            elif (
                hasattr(room, "player_description")
                and room.player_description
                and room.player_description.strip()
            ):
                room_description = room.player_description
            elif room.name and room.name.strip():
                room_description = f"Named '{room.name}'"

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

    def _build_allocated_content_context(self, allocated_content: dict) -> str:
        """Build context about allocated content for this room."""
        if not allocated_content:
            return ""

        context_parts = []

        # Add treasure context
        if allocated_content.get("treasures"):
            treasures = allocated_content["treasures"]
            treasure_info = []
            for treasure in treasures:
                tier = treasure.get("tier", "unknown")
                treasure_type = treasure.get("type", "unknown")
                value = treasure.get("base_value", 0)
                treasure_info.append(
                    f"- {tier.title()} {treasure_type} (value: {value})"
                )

            context_parts.append("ALLOCATED TREASURE:\n" + "\n".join(treasure_info))

        # Add monster context
        if allocated_content.get("monsters"):
            monsters = allocated_content["monsters"]
            monster_info = []
            for monster in monsters:
                cr = monster.get("challenge_rating", 1)
                monster_type = monster.get("monster_type", "unknown")
                group_size = monster.get("group_size", 1)
                difficulty = monster.get("encounter_difficulty", "medium")
                monster_info.append(
                    f"- {monster_type} (CR {cr}, group size {group_size}, {difficulty})"
                )

            context_parts.append("ALLOCATED MONSTERS:\n" + "\n".join(monster_info))

        # Add trap context
        if allocated_content.get("traps"):
            traps = allocated_content["traps"]
            trap_info = []
            for trap in traps:
                tier = trap.get("trap_tier", "unknown")
                trap_type = trap.get("trap_type", "unknown")
                dc = trap.get("dc", 10)
                damage = trap.get("damage", "1d4")
                danger = trap.get("danger_level", "medium")
                trap_info.append(
                    f"- {tier.title()} {trap_type} (DC {dc}, damage {damage}, {danger})"
                )

            context_parts.append("ALLOCATED TRAPS:\n" + "\n".join(trap_info))

        if context_parts:
            return "ALLOCATED CONTENT FOR THIS ROOM:\n" + "\n".join(context_parts)

        return ""
