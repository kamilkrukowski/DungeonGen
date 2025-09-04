"""
Monster encounter planning for dungeon content generation.
"""

from typing import Any

from opentelemetry import trace

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
        rooms_with_monsters: list = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Generate balanced monster encounters for the dungeon.

        Args:
            room_count: Number of rooms that need monsters
            guidelines: Dungeon generation guidelines
            options: Generation options
            rooms_with_monsters: List of rooms that need monster encounters

        Returns:
            Dictionary of monster encounters organized by room size categories
        """
        # Initialize encounters by room size
        encounters = {"boss": [], "large": [], "huge": [], "small": [], "tiny": []}

        # Count rooms by size category
        room_counts_by_size = self._count_rooms_by_size(rooms_with_monsters)

        # Generate encounters for each room size category
        for room_size_category, count in room_counts_by_size.items():
            if count > 0:
                # Generate encounters for this room size category
                # Add some buffer (n_rooms + 2) to ensure we have enough monsters
                encounters_to_generate = count + 2

                for i in range(encounters_to_generate):
                    encounter = self._generate_single_encounter(
                        room_index=i,
                        total_rooms=count,
                        guidelines=guidelines,
                    )
                    encounters[room_size_category].append(encounter)

        # Add span attributes for monster generation results
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute("monster_planner.room_count", room_count)

            # Add room counts by size category
            for category, count in room_counts_by_size.items():
                current_span.set_attribute(f"monster_planner.{category}_rooms", count)

            # Calculate total encounters across all categories
            total_encounters = sum(
                len(encounter_list) for encounter_list in encounters.values()
            )
            current_span.set_attribute(
                "monster_planner.total_encounters", total_encounters
            )

            # Add encounter counts by category
            for category, encounter_list in encounters.items():
                current_span.set_attribute(
                    f"monster_planner.{category}_encounters", len(encounter_list)
                )

            # Handle empty encounters case
            all_encounters = [
                encounter
                for encounter_list in encounters.values()
                for encounter in encounter_list
            ]
            if all_encounters:
                current_span.set_attribute(
                    "monster_planner.cr_range",
                    f"{min(e.get('challenge_rating', 0) for e in all_encounters)}-{max(e.get('challenge_rating', 0) for e in all_encounters)}",
                )
            else:
                current_span.set_attribute("monster_planner.cr_range", "N/A")

            # Difficulty is now sampled dynamically, no progression needed
            current_span.set_attribute("monster_planner.theme", guidelines.theme)
            current_span.set_attribute(
                "monster_planner.difficulty", guidelines.difficulty
            )

        return encounters

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
        guidelines: DungeonGuidelines,
    ) -> dict[str, Any]:
        """Generate a single monster encounter."""
        import random

        # Sample CR dynamically based on difficulty setting and theme
        base_multiplier = self._get_difficulty_multiplier(guidelines.difficulty)
        theme_adjustment = self._get_theme_difficulty_adjustment(guidelines.theme)
        difficulty_multiplier = base_multiplier * theme_adjustment

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
            # Standard encounters - extract weights from cr_tiers
            adjusted_weights = {
                tier: tier_data["weight"] for tier, tier_data in self.cr_tiers.items()
            }
        else:
            # Harder encounters
            adjusted_weights = {
                "easy": 0.2,
                "medium": 0.4,
                "hard": 0.3,
                "deadly": 0.1,
            }

        # Validate that all weights are numeric
        for tier, weight in adjusted_weights.items():
            if not isinstance(weight, int | float):
                raise ValueError(
                    f"Invalid weight for tier '{tier}': {weight} (type: {type(weight).__name__}). "
                    f"Weights must be numeric values, not {type(weight).__name__}."
                )

        # Convert to list for random selection
        tiers = list(adjusted_weights.keys())
        weights = list(adjusted_weights.values())

        return random.choices(tiers, weights=weights)[0]

    def _get_difficulty_multiplier(self, difficulty: str) -> float:
        """Get difficulty multiplier based on difficulty setting."""
        difficulty_multipliers = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.3,
            "deadly": 1.6,
        }
        return difficulty_multipliers.get(difficulty.lower(), 1.0)

    def _count_rooms_by_size(self, rooms_with_monsters: list) -> dict[str, int]:
        """Count rooms by size category."""
        counts = {"boss": 0, "large": 0, "huge": 0, "small": 0, "tiny": 0}

        if not rooms_with_monsters:
            return counts

        for room in rooms_with_monsters:
            room_size_category = self._get_room_size_category_from_room(room)
            counts[room_size_category] += 1

        return counts

    def _get_room_size_category_from_room(self, room) -> str:
        """Determine room size category based on actual room dimensions."""

        room_area = room.width * room.height

        # Use consistent categorization with the boss room sampler
        if room_area <= 12:  # 3x4 or smaller
            return "tiny"
        elif room_area <= 20:  # 4x5 or smaller
            return "small"
        elif room_area <= 42:  # 6x7 or smaller
            return "huge"  # Using "huge" for medium rooms to avoid confusion with boss rooms
        elif room_area <= 72:  # 8x9 or smaller
            return "large"
        else:  # Larger than 8x9
            return "huge"

    def _get_room_size_category_from_encounter(self, encounter: dict[str, Any]) -> str:
        """Determine room size category based on room assignment, not monster CR."""
        # This should be based on which room the encounter is assigned to
        # For now, we'll distribute encounters evenly across room size categories
        # In a real implementation, this would be based on the actual room assignment

        # Get room index to determine assignment
        room_index = encounter.get("room_index", 0)

        # Simple distribution: cycle through room size categories
        # This is a placeholder - in practice, this would be determined by the actual room size
        categories = ["tiny", "small", "huge", "large", "boss"]
        return categories[room_index % len(categories)]

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
