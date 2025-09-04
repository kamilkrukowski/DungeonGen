"""
Boss planning for dungeon content generation.
"""

import random
from typing import Any

try:
    from opentelemetry import trace
except ImportError:
    trace = None

from models.dungeon import DungeonGuidelines, GenerationOptions
from utils import simple_trace


class BossPlanner:
    """Plans boss encounters for dungeon content generation."""

    def __init__(self):
        """Initialize the boss planner."""
        # Boss types by theme and room size
        self.boss_types = {
            "temple": {
                "boss": ["High Priest", "Archbishop", "Divine Avatar"],
                "large": ["Temple Guardian", "Sacred Knight", "Celestial Being"],
                "huge": ["Ancient Deity", "Divine Construct", "Sacred Dragon"],
            },
            "tomb": {
                "boss": ["Lich King", "Mummy Lord", "Death Knight"],
                "large": ["Wraith Lord", "Bone Dragon", "Spectral Guardian"],
                "huge": ["Ancient Lich", "Death God Avatar", "Undead Dragon Lord"],
            },
            "mine": {
                "boss": ["Duergar King", "Earth Elemental Lord", "Deep Dragon"],
                "large": ["Stone Giant", "Iron Golem", "Cave Troll King"],
                "huge": [
                    "Ancient Earth Dragon",
                    "Mountain Giant",
                    "Deep Dwarf Overlord",
                ],
            },
            "fortress": {
                "boss": ["Warlord", "Knight Commander", "Battle Mage"],
                "large": ["War Golem", "Siege Engine", "Elite Guard Captain"],
                "huge": ["Ancient Warlord", "Fortress Dragon", "Legendary Knight"],
            },
            "lair": {
                "boss": ["Dragon", "Beast Lord", "Monstrosity King"],
                "large": ["Ancient Beast", "Dire Dragon", "Legendary Predator"],
                "huge": ["Elder Dragon", "Primordial Beast", "Legendary Monstrosity"],
            },
            "abandoned": {
                "boss": ["Rust Monster Queen", "Ooze Lord", "Construct Master"],
                "large": ["Ancient Construct", "Giant Ooze", "Rust Dragon"],
                "huge": [
                    "Primordial Construct",
                    "Elder Ooze",
                    "Legendary Rust Monster",
                ],
            },
        }

        # Boss CR ranges by room size
        self.boss_cr_ranges = {
            "boss": (8, 15),  # Standard boss range
            "large": (12, 18),  # Large room bosses
            "huge": (15, 22),  # Huge room bosses
        }

    @simple_trace("BossPlanner.generate_boss")
    def generate_boss(
        self,
        room_area: int,
        dungeon_name: str,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> dict[str, Any]:
        """
        Generate a boss encounter based on room size and dungeon context.

        Args:
            room_area: Area of the boss room (width * height)
            dungeon_name: Name of the dungeon
            guidelines: Dungeon generation guidelines
            options: Generation options

        Returns:
            Boss encounter data with metadata
        """
        # Determine room size category based on area
        room_size_category = self._get_room_size_category(room_area)

        # Get boss type based on theme and room size
        boss_type = self._select_boss_type(guidelines.theme, room_size_category)

        # Generate CR based on room size and difficulty
        challenge_rating = self._generate_boss_cr(
            room_size_category, guidelines.difficulty
        )

        # Generate boss name incorporating dungeon name
        boss_name = self._generate_boss_name(boss_type, dungeon_name, guidelines.theme)

        # Generate boss abilities and special features
        abilities = self._generate_boss_abilities(
            boss_type, challenge_rating, guidelines.theme
        )

        # Calculate boss difficulty
        boss_difficulty = self._calculate_boss_difficulty(
            challenge_rating, room_size_category
        )

        boss_data = {
            "boss_type": boss_type,
            "boss_name": boss_name,
            "challenge_rating": challenge_rating,
            "room_size_category": room_size_category,
            "room_area": room_area,
            "theme": guidelines.theme,
            "difficulty": guidelines.difficulty,
            "dungeon_name": dungeon_name,
            "abilities": abilities,
            "boss_difficulty": boss_difficulty,
            "is_boss": True,
            "generated": True,
        }

        # Add span attributes for boss generation
        current_span = trace.get_current_span() if trace else None
        if current_span:
            current_span.set_attribute("boss_planner.boss_type", boss_type)
            current_span.set_attribute("boss_planner.boss_name", boss_name)
            current_span.set_attribute(
                "boss_planner.challenge_rating", challenge_rating
            )
            current_span.set_attribute(
                "boss_planner.room_size_category", room_size_category
            )
            current_span.set_attribute("boss_planner.room_area", room_area)

        return boss_data

    def _get_room_size_category(self, room_area: int) -> str:
        """Determine room size category based on area."""
        if room_area <= 42:  # Medium room or smaller
            return "boss"  # Standard boss room
        elif room_area <= 72:  # Large room
            return "large"
        else:  # Huge room
            return "huge"

    def _select_boss_type(self, theme: str, room_size_category: str) -> str:
        """Select boss type based on theme and room size."""
        theme_bosses = self.boss_types.get(theme.lower(), self.boss_types["lair"])
        boss_options = theme_bosses.get(room_size_category, theme_bosses["boss"])
        return random.choice(boss_options)

    def _generate_boss_cr(self, room_size_category: str, difficulty: str) -> float:
        """Generate challenge rating based on room size and difficulty."""
        min_cr, max_cr = self.boss_cr_ranges[room_size_category]

        # Adjust CR based on difficulty
        difficulty_multipliers = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.2,
            "deadly": 1.4,
        }

        multiplier = difficulty_multipliers.get(difficulty.lower(), 1.0)
        adjusted_min = min_cr * multiplier
        adjusted_max = max_cr * multiplier

        return round(random.uniform(adjusted_min, adjusted_max), 1)

    def _generate_boss_name(self, boss_type: str, dungeon_name: str, theme: str) -> str:
        """Generate a boss name incorporating dungeon context."""
        # Extract key words from dungeon name
        dungeon_words = dungeon_name.split()
        dungeon_word = random.choice(dungeon_words) if dungeon_words else "Ancient"

        # Generate name variations
        name_templates = [
            f"{dungeon_word} {boss_type}",
            f"The {boss_type} of {dungeon_name}",
            f"{boss_type} {dungeon_word}",
            f"Lord {dungeon_word}",
            f"{dungeon_word} the {boss_type}",
        ]

        return random.choice(name_templates)

    def _generate_boss_abilities(
        self, boss_type: str, cr: float, theme: str
    ) -> list[str]:
        """Generate boss abilities based on type and CR."""
        abilities = []

        # Base abilities by CR
        if cr >= 15:
            abilities.extend(["Legendary Actions", "Lair Actions", "Magic Resistance"])
        elif cr >= 10:
            abilities.extend(["Legendary Actions", "Magic Resistance"])
        else:
            abilities.append("Magic Resistance")

        # Theme-specific abilities
        theme_abilities = {
            "temple": ["Divine Smite", "Turn Undead", "Sacred Aura"],
            "tomb": ["Undead Fortitude", "Necrotic Aura", "Animate Dead"],
            "mine": ["Earth Tremor", "Stone Shape", "Burrow"],
            "fortress": ["Battle Tactics", "Shield Wall", "Rally"],
            "lair": ["Frightful Presence", "Multiattack", "Legendary Resistance"],
            "abandoned": ["Rust Touch", "Corrosion", "Construct Resilience"],
        }

        theme_ability_list = theme_abilities.get(theme.lower(), [])
        if theme_ability_list:
            abilities.extend(
                random.sample(theme_ability_list, min(2, len(theme_ability_list)))
            )

        return abilities

    def _calculate_boss_difficulty(self, cr: float, room_size_category: str) -> str:
        """Calculate boss difficulty level."""
        # Adjust difficulty based on room size
        size_multipliers = {
            "boss": 1.0,
            "large": 1.2,
            "huge": 1.5,
        }

        adjusted_cr = cr * size_multipliers.get(room_size_category, 1.0)

        if adjusted_cr >= 18:
            return "legendary"
        elif adjusted_cr >= 15:
            return "epic"
        elif adjusted_cr >= 12:
            return "deadly"
        else:
            return "hard"
