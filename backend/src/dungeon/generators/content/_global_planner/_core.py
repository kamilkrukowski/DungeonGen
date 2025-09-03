"""
Main orchestrator for global dungeon content planning.
"""

from dataclasses import dataclass
from typing import Any

from opentelemetry import trace

from models.dungeon import DungeonGuidelines, DungeonLayout, GenerationOptions
from utils import simple_trace

from ._balance import BalanceCalculator
from ._monsters import MonsterPlanner
from ._name_generator import DungeonNameGenerator
from ._traps import TrapPlanner
from ._treasure import TreasurePlanner


@dataclass
class DungeonContentPlan:
    """Complete plan for dungeon content distribution."""

    name: str
    treasures: list[dict[str, Any]]
    monsters: list[dict[str, Any]]
    traps: list[dict[str, Any]]
    total_value: float
    difficulty_curve: list[float]


class GlobalPlanner:
    """
    Orchestrates global planning for dungeon content.

    This class coordinates the generation of treasure lists, monster encounters,
    and trap themes before they are allocated to individual rooms.
    """

    def __init__(self):
        """Initialize the global planner with specialized planners."""
        self.name_generator = DungeonNameGenerator()
        self.treasure_planner = TreasurePlanner()
        self.monster_planner = MonsterPlanner()
        self.trap_planner = TrapPlanner()
        self.balance_calculator = BalanceCalculator()

    @simple_trace("GlobalPlanner.plan_dungeon_content")
    def plan_dungeon_content(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> DungeonContentPlan:
        """
        Generate a complete plan for dungeon content distribution.

        Args:
            layout: Dungeon layout with rooms and content flags
            guidelines: Generation guidelines including content percentages
            options: Generation options

        Returns:
            Complete content plan with treasures, monsters, and traps
        """
        # Generate dungeon name first
        dungeon_name = self.name_generator.generate_dungeon_name(guidelines)

        # Count rooms that need each content type
        room_counts = self._analyze_room_requirements(layout)

        # Generate treasure list based on room count and guidelines
        treasure_list = self.treasure_planner.generate_treasure_list(
            room_count=room_counts["treasure"], guidelines=guidelines, options=options
        )

        # Generate monster encounters based on room count and difficulty
        monster_encounters = self.monster_planner.generate_encounters(
            room_count=room_counts["monsters"], guidelines=guidelines, options=options
        )

        # Generate trap themes based on room count and guidelines
        trap_themes = self.trap_planner.generate_trap_themes(
            room_count=room_counts["traps"], guidelines=guidelines, options=options
        )

        # Add span attributes for each generation stage
        current_span = trace.get_current_span()
        if current_span:
            # Treasure generation results
            current_span.set_attribute(
                "global_planner.treasure_count", len(treasure_list)
            )
            current_span.set_attribute(
                "global_planner.treasure_tiers",
                str([t.get("tier", "unknown") for t in treasure_list[:5]]),
            )  # First 5 for brevity
            current_span.set_attribute(
                "global_planner.treasure_total_value",
                sum(t.get("base_value", 0) for t in treasure_list),
            )

            # Monster generation results
            current_span.set_attribute(
                "global_planner.monster_count", len(monster_encounters)
            )

            # Handle empty monster_encounters case
            if monster_encounters:
                current_span.set_attribute(
                    "global_planner.monster_cr_range",
                    f"{min(e.get('challenge_rating', 0) for e in monster_encounters)}-{max(e.get('challenge_rating', 0) for e in monster_encounters)}",
                )
            else:
                current_span.set_attribute("global_planner.monster_cr_range", "N/A")

            current_span.set_attribute(
                "global_planner.monster_difficulty_distribution",
                str(
                    [
                        e.get("encounter_difficulty", "unknown")
                        for e in monster_encounters[:5]
                    ]
                ),
            )

            # Trap generation results
            current_span.set_attribute("global_planner.trap_count", len(trap_themes))
            current_span.set_attribute(
                "global_planner.trap_tier_distribution",
                str([t.get("trap_tier", "unknown") for t in trap_themes[:5]]),
            )

            # Handle empty trap_themes case
            if trap_themes:
                current_span.set_attribute(
                    "global_planner.trap_dc_range",
                    f"{min(t.get('dc', 0) for t in trap_themes)}-{max(t.get('dc', 0) for t in trap_themes)}",
                )
            else:
                current_span.set_attribute("global_planner.trap_dc_range", "N/A")

            # Overall planning results
            current_span.set_attribute("global_planner.dungeon_name", dungeon_name)
            current_span.set_attribute(
                "global_planner.room_requirements", str(room_counts)
            )

        # Calculate total value and difficulty curve
        total_value = self.balance_calculator.calculate_total_value(treasure_list)
        difficulty_curve = self.balance_calculator.calculate_difficulty_curve(
            monster_encounters, layout
        )

        return DungeonContentPlan(
            name=dungeon_name,
            treasures=treasure_list,
            monsters=monster_encounters,
            traps=trap_themes,
            total_value=total_value,
            difficulty_curve=difficulty_curve,
        )

    def _analyze_room_requirements(self, layout: DungeonLayout) -> dict[str, int]:
        """Analyze how many rooms need each content type."""
        return {
            "treasure": sum(1 for room in layout.rooms if room.has_treasure),
            "monsters": sum(1 for room in layout.rooms if room.has_monsters),
            "traps": sum(1 for room in layout.rooms if room.has_traps),
        }
