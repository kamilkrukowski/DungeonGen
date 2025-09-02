"""
Utility functions for dungeon generation.
"""

import re

from models.dungeon import DungeonGuidelines


def parse_user_guidelines(user_input: str) -> DungeonGuidelines:
    """
    Parse natural language user input into structured guidelines.

    Args:
        user_input: Natural language description of desired dungeon

    Returns:
        Structured DungeonGuidelines object
    """
    # Extract theme and atmosphere from user input
    theme = _extract_theme(user_input)
    atmosphere = _extract_atmosphere(user_input)
    difficulty = _extract_difficulty(user_input)
    room_count = _extract_room_count(user_input)

    # Extract special requirements
    special_requirements = _extract_special_requirements(user_input)

    return DungeonGuidelines(
        theme=theme,
        atmosphere=atmosphere,
        difficulty=difficulty,
        room_count=room_count,
        layout_type="line_graph",  # Default, will be overridden by options
        special_requirements=special_requirements,
    )


def _extract_theme(user_input: str) -> str:
    """Extract the main theme from user input."""
    input_lower = user_input.lower()

    # Common theme keywords
    themes = {
        "castle": ["castle", "fortress", "palace", "keep"],
        "cave": ["cave", "cavern", "underground", "tunnel"],
        "temple": ["temple", "shrine", "sanctuary", "church"],
        "dungeon": ["dungeon", "prison", "cellar", "basement"],
        "tower": ["tower", "spire", "turret"],
        "mansion": ["mansion", "manor", "estate", "house"],
        "crypt": ["crypt", "tomb", "necropolis", "graveyard"],
        "mine": ["mine", "quarry", "excavation"],
        "ruins": ["ruins", "ruined", "abandoned", "destroyed"],
        "lair": ["lair", "den", "nest", "hideout"],
    }

    for theme, keywords in themes.items():
        if any(keyword in input_lower for keyword in keywords):
            return theme

    # Default theme
    return "dungeon"


def _extract_atmosphere(user_input: str) -> str:
    """Extract the atmosphere from user input."""
    input_lower = user_input.lower()

    # Common atmosphere keywords
    atmospheres = {
        "haunted": ["haunted", "ghost", "spirit", "phantom", "specter"],
        "dark": ["dark", "shadowy", "gloomy", "dim"],
        "mysterious": ["mysterious", "enigmatic", "puzzling", "cryptic"],
        "dangerous": ["dangerous", "deadly", "hazardous", "treacherous"],
        "ancient": ["ancient", "old", "antique", "vintage"],
        "magical": ["magical", "enchanted", "mystical", "arcane"],
        "corrupted": ["corrupted", "tainted", "defiled", "polluted"],
        "abandoned": ["abandoned", "deserted", "empty", "vacant"],
        "lively": ["lively", "active", "busy", "populated"],
        "peaceful": ["peaceful", "calm", "serene", "tranquil"],
    }

    for atmosphere, keywords in atmospheres.items():
        if any(keyword in input_lower for keyword in keywords):
            return atmosphere

    # Default atmosphere
    return "mysterious"


def _extract_difficulty(user_input: str) -> str:
    """Extract the difficulty level from user input."""
    input_lower = user_input.lower()

    if any(word in input_lower for word in ["easy", "simple", "basic"]):
        return "easy"
    elif any(
        word in input_lower for word in ["hard", "difficult", "challenging", "deadly"]
    ):
        return "hard"
    else:
        return "medium"


def _extract_room_count(user_input: str) -> int:
    """Extract the desired room count from user input."""
    # Look for numbers followed by "room" or similar
    patterns = [
        r"(\d+)\s*rooms?",
        r"(\d+)\s*chambers?",
        r"(\d+)\s*areas?",
        r"(\d+)\s*levels?",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            count = int(match.group(1))
            # Clamp to reasonable range
            return max(3, min(20, count))

    # Default room count
    return 5


def _extract_special_requirements(user_input: str) -> list:
    """Extract special requirements from user input."""
    requirements = []
    input_lower = user_input.lower()

    # Common special requirements
    special_reqs = {
        "traps": ["trap", "pit", "pressure plate", "poison"],
        "puzzles": ["puzzle", "riddle", "mystery", "enigma"],
        "treasure": ["treasure", "loot", "gold", "jewel"],
        "monsters": ["monster", "creature", "beast", "enemy"],
        "npcs": ["npc", "character", "person", "merchant"],
        "secrets": ["secret", "hidden", "concealed", "undiscovered"],
        "water": ["water", "river", "lake", "pool", "flooded"],
        "fire": ["fire", "lava", "burning", "flame"],
        "ice": ["ice", "frozen", "cold", "frost"],
        "magic": ["magic", "spell", "enchantment", "ritual"],
    }

    for req, keywords in special_reqs.items():
        if any(keyword in input_lower for keyword in keywords):
            requirements.append(req)

    return requirements
