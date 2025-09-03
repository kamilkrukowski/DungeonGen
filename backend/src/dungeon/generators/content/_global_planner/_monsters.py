"""
Monster encounter planning for dungeon content generation.
"""

from typing import Any

from models.dungeon import DungeonGuidelines, GenerationOptions
from utils import simple_trace


class MonsterPlanner:
    """Plans monster encounters across the dungeon."""

    def __init__(self):
        """Initialize the monster planner."""
        # Define CR tiers and their characteristics
        self.cr_tiers = {
            "easy": {"min_cr": 0.125, "max_cr": 2, "weight": 0.5, "group_size": (1, 4)},
            "medium": {"min_cr": 1, "max_cr": 5, "weight": 0.3, "group_size": (1, 3)},
            "hard": {"min_cr": 3, "max_cr": 8, "weight": 0.15, "group_size": (1, 2)},
            "deadly": {"min_cr": 6, "max_cr": 12, "weight": 0.05, "group_size": (1, 1)},
        }

    @simple_trace("MonsterPlanner.generate_encounters")
    def generate_encounters(
        self,
        room_count: int,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> list[dict[str, Any]]:
        """
        Generate balanced monster encounters for the dungeon.

        Args:
            room_count: Number of rooms that need monsters
            guidelines: Dungeon generation guidelines
            options: Generation options

        Returns:
            List of monster encounters with metadata
        """
        encounters = []

        # Calculate difficulty progression based on dungeon size and theme
        difficulty_progression = self._calculate_difficulty_progression(
            room_count, guidelines
        )

        # Generate encounters for each room
        for i in range(room_count):
            encounter = self._generate_single_encounter(
                room_index=i,
                total_rooms=room_count,
                difficulty_progression=difficulty_progression,
                guidelines=guidelines,
            )
            encounters.append(encounter)

        return encounters

    def _calculate_difficulty_progression(
        self, room_count: int, guidelines: DungeonGuidelines
    ) -> list[float]:
        """Calculate how difficulty should progress through the dungeon."""

        # Base difficulty multiplier based on overall difficulty setting
        base_multiplier = self._get_difficulty_multiplier(guidelines.difficulty)

        # Create a progression curve (easier at start, harder at end)
        progression = []

        for i in range(room_count):
            # Use a sigmoid-like curve for smooth progression
            progress = i / max(room_count - 1, 1)
            difficulty_multiplier = 0.5 + (progress * 1.5)  # 0.5x to 2.0x

            # Apply theme-specific adjustments
            theme_adjustment = self._get_theme_difficulty_adjustment(guidelines.theme)

            final_multiplier = (
                difficulty_multiplier * base_multiplier * theme_adjustment
            )

            progression.append(final_multiplier)

        return progression

    def _get_difficulty_multiplier(self, difficulty: str) -> float:
        """Get base difficulty multiplier."""
        multipliers = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.4,
            "deadly": 2.0,
        }
        return multipliers.get(difficulty.lower(), 1.0)

    def _get_theme_difficulty_adjustment(self, theme: str) -> float:
        """Get theme-specific difficulty adjustment."""
        adjustments = {
            "abandoned": 0.8,  # Abandoned places are less dangerous
            "lair": 1.3,  # Monster lairs are more dangerous
            "temple": 1.1,  # Temples have some guardians
            "tomb": 1.2,  # Tombs have undead and traps
            "mine": 0.9,  # Mines might have some creatures
            "fortress": 1.0,  # Standard military difficulty
        }
        return adjustments.get(theme.lower(), 1.0)

    def _generate_single_encounter(
        self,
        room_index: int,
        total_rooms: int,
        difficulty_progression: list[float],
        guidelines: DungeonGuidelines,
    ) -> dict[str, Any]:
        """Generate a single monster encounter."""
        import random

        # Get difficulty multiplier for this room
        difficulty_multiplier = difficulty_progression[room_index]

        # Select CR tier based on difficulty and weights
        cr_tier = self._select_cr_tier(difficulty_multiplier)
        tier_config = self.cr_tiers[cr_tier]

        # Generate CR within the tier range
        cr = random.uniform(tier_config["min_cr"], tier_config["max_cr"])

        # Determine group size
        min_size, max_size = tier_config["group_size"]
        group_size = random.randint(min_size, max_size)

        # Generate monster type based on theme and CR
        monster_type = self._generate_monster_type(cr, guidelines.theme)

        # Calculate encounter difficulty
        encounter_difficulty = self._calculate_encounter_difficulty(
            cr, group_size, difficulty_multiplier
        )

        return {
            "cr_tier": cr_tier,
            "challenge_rating": round(cr, 2),
            "group_size": group_size,
            "monster_type": monster_type,
            "theme": guidelines.theme,
            "difficulty": guidelines.difficulty,
            "encounter_difficulty": encounter_difficulty,
            "room_index": room_index,
            "generated": True,
        }

    def _select_cr_tier(self, difficulty_multiplier: float) -> str:
        """Select CR tier based on difficulty multiplier."""
        import random

        # Adjust weights based on difficulty multiplier
        adjusted_weights = {}

        if difficulty_multiplier < 0.8:
            # Easier encounters
            adjusted_weights = {
                "easy": 0.7,
                "medium": 0.25,
                "hard": 0.05,
                "deadly": 0.0,
            }
        elif difficulty_multiplier < 1.2:
            # Standard encounters
            adjusted_weights = self.cr_tiers
        else:
            # Harder encounters
            adjusted_weights = {
                "easy": 0.2,
                "medium": 0.4,
                "hard": 0.3,
                "deadly": 0.1,
            }

        # Convert to list for random selection
        tiers = list(adjusted_weights.keys())
        weights = list(adjusted_weights.values())

        return random.choices(tiers, weights=weights)[0]

    def _generate_monster_type(self, cr: float, theme: str) -> str:
        """Generate monster type based on CR and theme."""
        import random

        # Base monster types by CR range
        if cr < 1:
            base_types = ["rats", "spiders", "bats", "snakes"]
        elif cr < 3:
            base_types = ["goblins", "kobolds", "skeletons", "zombies"]
        elif cr < 6:
            base_types = ["orcs", "hobgoblins", "ghouls", "wights"]
        elif cr < 9:
            base_types = ["trolls", "ogres", "vampires", "demons"]
        else:
            base_types = ["dragons", "giants", "liches", "beholders"]

        # Theme-specific adjustments
        theme_types = self._get_theme_monster_types(theme)
        if theme_types:
            base_types.extend(theme_types)

        return random.choice(base_types)

    def _get_theme_monster_types(self, theme: str) -> list[str]:
        """Get theme-specific monster types."""
        theme_monsters = {
            "temple": ["clerics", "paladins", "angels", "devils"],
            "tomb": ["mummies", "wraiths", "specters", "ghosts"],
            "mine": ["dwarves", "duergar", "elementals", "constructs"],
            "fortress": ["soldiers", "knights", "archers", "wizards"],
            "lair": ["beasts", "dragons", "monstrosities", "aberrations"],
            "abandoned": ["vermin", "ooze", "plants", "constructs"],
        }
        return theme_monsters.get(theme.lower(), [])

    def _calculate_encounter_difficulty(
        self, cr: float, group_size: int, difficulty_multiplier: float
    ) -> float:
        """Calculate overall encounter difficulty."""
        # Base difficulty is CR * group size
        base_difficulty = cr * group_size

        # Apply difficulty multiplier
        adjusted_difficulty = base_difficulty * difficulty_multiplier

        # Categorize difficulty
        if adjusted_difficulty < 2:
            return "easy"
        elif adjusted_difficulty < 6:
            return "medium"
        elif adjusted_difficulty < 12:
            return "hard"
        else:
            return "deadly"
