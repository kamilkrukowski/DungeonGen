"""
Trap planning for dungeon content generation.
"""

from typing import Any

from opentelemetry import trace

from models.dungeon import DungeonGuidelines, GenerationOptions
from utils import simple_trace


class TrapPlanner:
    """Plans trap distribution across the dungeon."""

    def __init__(self):
        """Initialize the trap planner."""
        # Define trap tiers and their characteristics
        self.trap_tiers = {
            "simple": {
                "dc": (10, 13),
                "damage": "1d4",
                "weight": 0.5,
                "complexity": "basic",
            },
            "moderate": {
                "dc": (12, 16),
                "damage": "2d6",
                "weight": 0.3,
                "complexity": "intermediate",
            },
            "complex": {
                "dc": (15, 18),
                "damage": "4d8",
                "weight": 0.15,
                "complexity": "advanced",
            },
            "deadly": {
                "dc": (18, 22),
                "damage": "6d10",
                "weight": 0.05,
                "complexity": "expert",
            },
        }

    @simple_trace("TrapPlanner.generate_trap_themes")
    def generate_trap_themes(
        self,
        room_count: int,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> list[dict[str, Any]]:
        """
        Generate trap themes and patterns for the dungeon.

        Args:
            room_count: Number of rooms that need traps
            guidelines: Dungeon generation guidelines
            options: Generation options

        Returns:
            List of trap themes with metadata
        """
        trap_themes = []

        # Calculate trap progression based on dungeon theme and difficulty
        trap_progression = self._calculate_trap_progression(room_count, guidelines)

        # Generate trap themes for each room
        for i in range(room_count):
            trap_theme = self._generate_single_trap_theme(
                room_index=i,
                total_rooms=room_count,
                trap_progression=trap_progression,
                guidelines=guidelines,
            )
            trap_themes.append(trap_theme)

        # Add span attributes for trap generation results
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute("trap_planner.room_count", room_count)
            current_span.set_attribute("trap_planner.total_traps", len(trap_themes))

            # Handle empty trap_themes case
            if trap_themes:
                current_span.set_attribute(
                    "trap_planner.dc_range",
                    f"{min(t.get('dc', 0) for t in trap_themes)}-{max(t.get('dc', 0) for t in trap_themes)}",
                )
                current_span.set_attribute(
                    "trap_planner.tier_distribution",
                    str([t.get("trap_tier", "unknown") for t in trap_themes[:5]]),
                )  # First 5 for brevity
            else:
                current_span.set_attribute("trap_planner.dc_range", "N/A")
                current_span.set_attribute("trap_planner.tier_distribution", "[]")

            current_span.set_attribute("trap_planner.theme", guidelines.theme)
            current_span.set_attribute("trap_planner.difficulty", guidelines.difficulty)

        return trap_themes

    def _calculate_trap_progression(
        self, room_count: int, guidelines: DungeonGuidelines
    ) -> list[float]:
        """Calculate how trap difficulty should progress through the dungeon."""

        # Base difficulty multiplier based on overall difficulty setting
        base_multiplier = self._get_difficulty_multiplier(guidelines.difficulty)

        # Create a progression curve (easier at start, harder at end)
        progression = []

        for i in range(room_count):
            # Use a linear progression for traps (more predictable than monsters)
            progress = i / max(room_count - 1, 1)
            difficulty_multiplier = 0.6 + (progress * 1.4)  # 0.6x to 2.0x

            # Apply theme-specific adjustments
            theme_adjustment = self._get_theme_trap_adjustment(guidelines.theme)

            final_multiplier = (
                difficulty_multiplier * base_multiplier * theme_adjustment
            )

            progression.append(final_multiplier)

        return progression

    def _get_difficulty_multiplier(self, difficulty: str) -> float:
        """Get base difficulty multiplier for traps."""
        multipliers = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.3,
            "deadly": 1.8,
        }
        return multipliers.get(difficulty.lower(), 1.0)

    def _get_theme_trap_adjustment(self, theme: str) -> float:
        """Get theme-specific trap adjustment."""
        adjustments = {
            "abandoned": 0.7,  # Abandoned places have fewer maintained traps
            "lair": 0.9,  # Monster lairs have some natural traps
            "temple": 1.2,  # Temples have protective traps
            "tomb": 1.4,  # Tombs are heavily trapped
            "mine": 0.8,  # Mines have some natural hazards
            "fortress": 1.1,  # Fortresses have defensive traps
        }
        return adjustments.get(theme.lower(), 1.0)

    def _generate_single_trap_theme(
        self,
        room_index: int,
        total_rooms: int,
        trap_progression: list[float],
        guidelines: DungeonGuidelines,
    ) -> dict[str, Any]:
        """Generate a single trap theme."""
        import random

        # Get difficulty multiplier for this room
        difficulty_multiplier = trap_progression[room_index]

        # Select trap tier based on difficulty and weights
        trap_tier = self._select_trap_tier(difficulty_multiplier)
        tier_config = self.trap_tiers[trap_tier]

        # Generate DC within the tier range
        dc = random.randint(tier_config["dc"][0], tier_config["dc"][1])

        # Generate trap type based on theme and tier
        trap_type = self._generate_trap_type(trap_tier, guidelines.theme)

        # Generate trigger mechanism
        trigger = self._generate_trigger_mechanism(trap_tier, guidelines.theme)

        # Calculate trap danger level
        danger_level = self._calculate_trap_danger(
            dc, tier_config["damage"], difficulty_multiplier
        )

        return {
            "trap_tier": trap_tier,
            "dc": dc,
            "damage": tier_config["damage"],
            "complexity": tier_config["complexity"],
            "trap_type": trap_type,
            "trigger": trigger,
            "theme": guidelines.theme,
            "difficulty": guidelines.difficulty,
            "danger_level": danger_level,
            "room_index": room_index,
            "generated": True,
        }

    def _select_trap_tier(self, difficulty_multiplier: float) -> str:
        """Select trap tier based on difficulty multiplier."""
        import random

        # Adjust weights based on difficulty multiplier
        if difficulty_multiplier < 0.8:
            # Easier traps
            adjusted_weights = {
                "simple": 0.8,
                "moderate": 0.2,
                "complex": 0.0,
                "deadly": 0.0,
            }
        elif difficulty_multiplier < 1.2:
            # Standard traps
            adjusted_weights = {
                "simple": 0.5,
                "moderate": 0.3,
                "complex": 0.15,
                "deadly": 0.05,
            }
        else:
            # Harder traps
            adjusted_weights = {
                "simple": 0.2,
                "moderate": 0.4,
                "complex": 0.3,
                "deadly": 0.1,
            }

        # Convert to list for random selection
        tiers = list(adjusted_weights.keys())
        weights = list(adjusted_weights.values())

        return random.choices(tiers, weights=weights)[0]

    def _generate_trap_type(self, tier: str, theme: str) -> str:
        """Generate trap type based on tier and theme."""
        import random

        # Base trap types by tier
        tier_types = {
            "simple": ["pressure_plate", "tripwire", "falling_rock", "poison_needle"],
            "moderate": ["swinging_blade", "poison_gas", "falling_floor", "arrow_trap"],
            "complex": [
                "magical_ward",
                "complex_mechanism",
                "illusion_trap",
                "teleport_trap",
            ],
            "deadly": ["crushing_walls", "lava_pit", "disintegration_ray", "time_loop"],
        }

        # Get available types for this tier
        available_types = tier_types.get(tier, ["pressure_plate"])

        # Theme-specific adjustments
        theme_types = self._get_theme_trap_types(theme)
        if theme_types:
            available_types.extend(theme_types)

        return random.choice(available_types)

    def _get_theme_trap_types(self, theme: str) -> list[str]:
        """Get theme-specific trap types."""
        theme_traps = {
            "temple": ["holy_ward", "consecrated_ground", "divine_retribution"],
            "tomb": ["curse_trap", "undead_guardian", "soul_drain"],
            "mine": ["cave_in", "gas_pocket", "unstable_support"],
            "fortress": ["defensive_mechanism", "alarm_system", "killing_ground"],
            "lair": ["natural_hazard", "beast_trap", "territorial_marker"],
            "abandoned": ["decay_hazard", "unstable_structure", "time_worn_mechanism"],
        }
        return theme_traps.get(theme.lower(), [])

    def _generate_trigger_mechanism(self, tier: str, theme: str) -> str:
        """Generate trigger mechanism for the trap."""
        import random

        # Base triggers by tier
        tier_triggers = {
            "simple": ["step", "touch", "proximity", "weight"],
            "moderate": ["magical_detection", "sound", "light", "movement"],
            "complex": ["pattern_recognition", "multi_condition", "delayed_trigger"],
            "deadly": ["intelligent_detection", "remote_activation", "chain_reaction"],
        }

        # Get available triggers for this tier
        available_triggers = tier_triggers.get(tier, ["step"])

        # Theme-specific adjustments
        theme_triggers = self._get_theme_triggers(theme)
        if theme_triggers:
            available_triggers.extend(theme_triggers)

        return random.choice(available_triggers)

    def _get_theme_triggers(self, theme: str) -> list[str]:
        """Get theme-specific trigger mechanisms."""
        theme_triggers = {
            "temple": ["profane_action", "unholy_presence", "sacrilegious_behavior"],
            "tomb": ["grave_robbery", "disturbing_rest", "breaking_seals"],
            "mine": ["mining_activity", "structural_stress", "mineral_detection"],
            "fortress": ["enemy_detection", "breach_attempt", "unauthorized_access"],
            "lair": ["territory_violation", "prey_detection", "threat_assessment"],
            "abandoned": [
                "structural_instability",
                "time_based",
                "environmental_change",
            ],
        }
        return theme_triggers.get(theme.lower(), [])

    def _calculate_trap_danger(
        self, dc: int, damage: str, difficulty_multiplier: float
    ) -> str:
        """Calculate overall trap danger level."""
        # Base danger is DC + damage complexity
        base_danger = dc

        # Apply difficulty multiplier
        adjusted_danger = base_danger * difficulty_multiplier

        # Categorize danger
        if adjusted_danger < 15:
            return "low"
        elif adjusted_danger < 20:
            return "medium"
        elif adjusted_danger < 25:
            return "high"
        else:
            return "extreme"
