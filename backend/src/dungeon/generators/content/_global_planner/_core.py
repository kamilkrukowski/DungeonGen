"""
Main orchestrator for global dungeon content planning.
"""

from dataclasses import dataclass
from typing import Any

from models.dungeon import DungeonGuidelines, DungeonLayout, GenerationOptions
from utils import simple_trace

from ._balance import BalanceCalculator
from ._monsters import MonsterPlanner
from ._traps import TrapPlanner
from ._treasure import TreasurePlanner


@dataclass
class DungeonContentPlan:
    """Complete plan for dungeon content distribution."""

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

        # Calculate total value and difficulty curve
        total_value = self.balance_calculator.calculate_total_value(treasure_list)
        difficulty_curve = self.balance_calculator.calculate_difficulty_curve(
            monster_encounters, layout
        )

        return DungeonContentPlan(
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
