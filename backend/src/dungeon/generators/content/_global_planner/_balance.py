"""
Balance calculations for dungeon content generation.
"""

from typing import Any

from models.dungeon import DungeonLayout
from utils import simple_trace


class BalanceCalculator:
    """Calculates balance metrics for dungeon content."""

    def __init__(self):
        """Initialize the balance calculator."""
        pass

    @simple_trace("BalanceCalculator.calculate_total_value")
    def calculate_total_value(self, treasure_list: list[dict[str, Any]]) -> float:
        """
        Calculate total treasure value for the dungeon.

        Args:
            treasure_list: List of treasure items with base_value

        Returns:
            Total calculated value
        """
        total_value = 0.0

        for treasure in treasure_list:
            if isinstance(treasure.get("base_value"), int | float):
                total_value += treasure["base_value"]

        return round(total_value, 2)

    @simple_trace("BalanceCalculator.calculate_difficulty_curve")
    def calculate_difficulty_curve(
        self, monster_encounters: list[dict[str, Any]], layout: DungeonLayout
    ) -> list[float]:
        """
        Calculate difficulty progression curve for the dungeon.

        Args:
            monster_encounters: List of monster encounters
            layout: Dungeon layout for spatial context

        Returns:
            List of difficulty values for each room
        """
        difficulty_curve = []

        # Create a difficulty value for each room in the layout
        for room in layout.rooms:
            room_difficulty = self._calculate_room_difficulty(room, monster_encounters)
            difficulty_curve.append(room_difficulty)

        return difficulty_curve

    def _calculate_room_difficulty(
        self, room: Any, monster_encounters: list[dict[str, Any]]
    ) -> float:
        """Calculate difficulty for a specific room."""
        # Find if this room has a monster encounter
        room_encounter = None
        for encounter in monster_encounters:
            if encounter.get("room_index") == room.id:
                room_encounter = encounter
                break

        if not room_encounter:
            return 0.0  # No monsters = no difficulty

        # Calculate base difficulty from CR and group size
        cr = room_encounter.get("challenge_rating", 1.0)
        group_size = room_encounter.get("group_size", 1)

        # Base difficulty formula: CR * group_size^0.5 (diminishing returns for large groups)
        import math

        base_difficulty = cr * math.sqrt(group_size)

        # Apply encounter difficulty multiplier
        difficulty_multiplier = self._get_encounter_difficulty_multiplier(
            room_encounter.get("encounter_difficulty", "medium")
        )

        return round(base_difficulty * difficulty_multiplier, 2)

    def _get_encounter_difficulty_multiplier(self, difficulty: str) -> float:
        """Get multiplier for encounter difficulty level."""
        multipliers = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.4,
            "deadly": 2.0,
        }
        return multipliers.get(difficulty.lower(), 1.0)

    def validate_content_balance(
        self,
        treasure_list: list[dict[str, Any]],
        monster_encounters: list[dict[str, Any]],
        trap_themes: list[dict[str, Any]],
        layout: DungeonLayout,
    ) -> dict[str, Any]:
        """
        Validate that the generated content is well-balanced.

        Args:
            treasure_list: List of treasure items
            monster_encounters: List of monster encounters
            trap_themes: List of trap themes
            layout: Dungeon layout

        Returns:
            Validation results with warnings and suggestions
        """
        validation_results = {
            "is_balanced": True,
            "warnings": [],
            "suggestions": [],
            "metrics": {},
        }

        # Calculate metrics
        total_treasure_value = self.calculate_total_value(treasure_list)
        difficulty_curve = self.calculate_difficulty_curve(monster_encounters, layout)

        # Store metrics
        validation_results["metrics"] = {
            "total_treasure_value": total_treasure_value,
            "difficulty_curve": difficulty_curve,
            "treasure_count": len(treasure_list),
            "monster_count": len(monster_encounters),
            "trap_count": len(trap_themes),
        }

        # Validate treasure distribution
        treasure_warnings = self._validate_treasure_distribution(treasure_list)
        validation_results["warnings"].extend(treasure_warnings)

        # Validate monster progression
        monster_warnings = self._validate_monster_progression(monster_encounters)
        validation_results["warnings"].extend(monster_warnings)

        # Validate trap distribution
        trap_warnings = self._validate_trap_distribution(trap_themes)
        validation_results["warnings"].extend(trap_warnings)

        # Check overall balance
        if validation_results["warnings"]:
            validation_results["is_balanced"] = False

        # Generate suggestions for improvement
        validation_results["suggestions"] = self._generate_balance_suggestions(
            treasure_list, monster_encounters, trap_themes, layout
        )

        return validation_results

    def _validate_treasure_distribution(
        self, treasure_list: list[dict[str, Any]]
    ) -> list[str]:
        """Validate treasure distribution balance."""
        warnings = []

        if not treasure_list:
            return warnings

        # Check for value clustering
        values = [t.get("base_value", 0) for t in treasure_list]
        values.sort()

        # Check if there's a huge gap between highest and lowest values
        value_range = max(values) - min(values)
        if value_range > 1000:
            warnings.append(
                "Large treasure value gap detected - consider more balanced distribution"
            )

        # Check tier distribution
        tier_counts = {}
        for treasure in treasure_list:
            tier = treasure.get("tier", "unknown")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Warn if too many high-tier items
        if tier_counts.get("major", 0) > len(treasure_list) * 0.2:
            warnings.append("Too many major treasure items - may unbalance the dungeon")

        return warnings

    def _validate_monster_progression(
        self, monster_encounters: list[dict[str, Any]]
    ) -> list[str]:
        """Validate monster encounter progression."""
        warnings = []

        if not monster_encounters:
            return warnings

        # Check for difficulty spikes
        crs = [e.get("challenge_rating", 1) for e in monster_encounters]
        crs.sort()

        for i in range(1, len(crs)):
            cr_jump = crs[i] - crs[i - 1]
            if cr_jump > 4:
                warnings.append(
                    f"Large CR jump detected ({crs[i-1]} to {crs[i]}) - may cause difficulty spike"
                )

        # Check if encounters get progressively harder
        if len(crs) > 2:
            first_half_avg = sum(crs[: len(crs) // 2]) / (len(crs) // 2)
            second_half_avg = sum(crs[len(crs) // 2 :]) / (len(crs) - len(crs) // 2)

            if second_half_avg < first_half_avg:
                warnings.append(
                    "Monster encounters don't show clear difficulty progression"
                )

        return warnings

    def _validate_trap_distribution(
        self, trap_themes: list[dict[str, Any]]
    ) -> list[str]:
        """Validate trap distribution balance."""
        warnings = []

        if not trap_themes:
            return warnings

        # Check for DC clustering
        dcs = [t.get("dc", 10) for t in trap_themes]
        dcs.sort()

        # Check if there's a huge gap between highest and lowest DCs
        dc_range = max(dcs) - min(dcs)
        if dc_range > 8:
            warnings.append(
                "Large trap DC gap detected - consider more balanced distribution"
            )

        # Check tier distribution
        tier_counts = {}
        for trap in trap_themes:
            tier = trap.get("trap_tier", "unknown")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Warn if too many deadly traps
        if tier_counts.get("deadly", 0) > len(trap_themes) * 0.15:
            warnings.append("Too many deadly traps - may make dungeon too difficult")

        return warnings

    def _generate_balance_suggestions(
        self,
        treasure_list: list[dict[str, Any]],
        monster_encounters: list[dict[str, Any]],
        trap_themes: list[dict[str, Any]],
        layout: DungeonLayout,
    ) -> list[str]:
        """Generate suggestions for improving balance."""
        suggestions = []

        # Treasure suggestions
        if treasure_list:
            total_value = self.calculate_total_value(treasure_list)
            room_count = len(layout.rooms)
            avg_value_per_room = total_value / room_count

            if avg_value_per_room < 100:
                suggestions.append(
                    "Consider increasing treasure value - current average is quite low"
                )
            elif avg_value_per_room > 800:
                suggestions.append(
                    "Consider reducing treasure value - current average is quite high"
                )

        # Monster suggestions
        if monster_encounters:
            crs = [e.get("challenge_rating", 1) for e in monster_encounters]
            if max(crs) - min(crs) < 2:
                suggestions.append(
                    "Consider more varied monster challenge ratings for better progression"
                )

        # Trap suggestions
        if trap_themes:
            dcs = [t.get("dc", 10) for t in trap_themes]
            if max(dcs) - min(dcs) < 4:
                suggestions.append(
                    "Consider more varied trap DCs for better challenge variety"
                )

        return suggestions
