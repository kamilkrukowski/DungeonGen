"""
Treasure planning for dungeon content generation.
"""

from typing import Any

from models.dungeon import DungeonGuidelines, GenerationOptions
from utils import simple_trace


class TreasurePlanner:
    """Plans treasure distribution across the dungeon."""

    def __init__(self):
        """Initialize the treasure planner."""
        # Define treasure tiers and their value ranges
        self.treasure_tiers = {
            "minor": {"min_value": 10, "max_value": 100, "weight": 0.6},
            "moderate": {"min_value": 100, "max_value": 500, "weight": 0.3},
            "major": {"min_value": 500, "max_value": 2000, "weight": 0.1},
        }

    @simple_trace("TreasurePlanner.generate_treasure_list")
    def generate_treasure_list(
        self,
        room_count: int,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> list[dict[str, Any]]:
        """
        Generate a balanced treasure list for the dungeon.

        Args:
            room_count: Number of rooms that need treasure
            guidelines: Dungeon generation guidelines
            options: Generation options

        Returns:
            List of treasure items with metadata
        """
        treasure_list = []

        # Calculate target total value based on difficulty and room count
        target_total = self._calculate_target_total_value(room_count, guidelines)

        # Distribute treasure across tiers
        tier_distribution = self._calculate_tier_distribution(room_count, target_total)

        for tier_name, count in tier_distribution.items():
            tier_config = self.treasure_tiers[tier_name]

            for _ in range(count):
                treasure_item = self._generate_treasure_item(
                    tier_name, tier_config, guidelines
                )
                treasure_list.append(treasure_item)

        # Ensure we have exactly the right number of items
        while len(treasure_list) < room_count:
            # Add minor treasures to fill remaining slots
            treasure_item = self._generate_treasure_item(
                "minor", self.treasure_tiers["minor"], guidelines
            )
            treasure_list.append(treasure_item)

        # Shuffle the list to avoid predictable distribution
        import random

        random.shuffle(treasure_list)

        return treasure_list

    def _calculate_target_total_value(
        self, room_count: int, guidelines: DungeonGuidelines
    ) -> float:
        """Calculate target total treasure value based on difficulty."""
        base_value_per_room = {
            "easy": 150,
            "medium": 300,
            "hard": 600,
            "deadly": 1000,
        }

        difficulty = guidelines.difficulty.lower()
        base_value = base_value_per_room.get(difficulty, 300)

        # Adjust for theme (some themes might have more/less treasure)
        theme_multiplier = self._get_theme_multiplier(guidelines.theme)

        return base_value * room_count * theme_multiplier

    def _get_theme_multiplier(self, theme: str) -> float:
        """Get treasure multiplier based on dungeon theme."""
        theme_multipliers = {
            "abandoned": 0.7,  # Less treasure in abandoned places
            "lair": 1.2,  # More treasure in monster lairs
            "temple": 1.5,  # Religious sites often have valuable items
            "tomb": 1.3,  # Tombs have burial goods
            "mine": 0.8,  # Mines might have some valuable minerals
            "fortress": 1.0,  # Standard military fortresses
        }

        return theme_multipliers.get(theme.lower(), 1.0)

    def _calculate_tier_distribution(
        self, room_count: int, target_total: float
    ) -> dict[str, int]:
        """Calculate how many items of each tier to generate."""
        distribution = {"minor": 0, "moderate": 0, "major": 0}

        # Start with base distribution based on weights
        total_items = max(room_count, 1)

        for tier_name, config in self.treasure_tiers.items():
            count = max(1, int(total_items * config["weight"]))
            distribution[tier_name] = min(count, room_count)

        # Adjust to ensure we don't exceed room count
        total_allocated = sum(distribution.values())
        if total_allocated > room_count:
            # Reduce from minor tier first
            excess = total_allocated - room_count
            distribution["minor"] = max(0, distribution["minor"] - excess)

        return distribution

    def _generate_treasure_item(
        self, tier: str, tier_config: dict[str, Any], guidelines: DungeonGuidelines
    ) -> dict[str, Any]:
        """Generate a single treasure item."""
        import random

        # Generate value within tier range
        value = random.uniform(tier_config["min_value"], tier_config["max_value"])

        # Generate treasure type based on theme and tier
        treasure_type = self._generate_treasure_type(tier, guidelines.theme)

        return {
            "tier": tier,
            "type": treasure_type,
            "base_value": round(value, 2),
            "theme": guidelines.theme,
            "difficulty": guidelines.difficulty,
            "generated": True,  # Flag to indicate this is a generated item
        }

    def _generate_treasure_type(self, tier: str, theme: str) -> str:
        """Generate treasure type based on tier and theme."""
        import random

        # Define treasure types by tier
        tier_types = {
            "minor": ["coins", "gems", "jewelry", "art", "weapons", "armor"],
            "moderate": [
                "magical_items",
                "precious_metals",
                "rare_gems",
                "ancient_artifacts",
            ],
            "major": [
                "legendary_weapons",
                "crown_jewels",
                "ancient_tomes",
                "divine_relics",
            ],
        }

        # Get available types for this tier
        available_types = tier_types.get(tier, ["coins"])

        # Theme-specific adjustments
        if theme.lower() == "temple":
            available_types.extend(["religious_symbols", "blessed_items"])
        elif theme.lower() == "tomb":
            available_types.extend(["burial_goods", "funerary_masks"])
        elif theme.lower() == "mine":
            available_types.extend(["precious_minerals", "crystal_clusters"])

        return random.choice(available_types)
