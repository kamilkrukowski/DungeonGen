"""
Main orchestrator for global dungeon content planning.
"""

from dataclasses import dataclass
from typing import Any

try:
    from opentelemetry import trace
except ImportError:
    trace = None

from models.dungeon import DungeonGuidelines, DungeonLayout, GenerationOptions
from utils import simple_trace

from ._balance import BalanceCalculator
from ._boss import BossPlanner
from ._monsters import MonsterPlanner
from ._name_generator import DungeonNameGenerator
from ._traps import TrapPlanner
from ._treasure import TreasurePlanner


@dataclass
class DungeonContentPlan:
    """Complete plan for dungeon content distribution."""

    name: str
    treasures: list[dict[str, Any]]
    monsters: dict[str, list[dict[str, Any]]]  # Keyed by room size categories
    traps: list[dict[str, Any]]
    boss: dict[str, Any] | None  # Boss encounter data
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
        self.boss_planner = BossPlanner()
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

        # Get rooms that need monster encounters
        rooms_with_monsters = [room for room in layout.rooms if room.has_monsters]

        # Generate monster encounters based on room count and difficulty
        monster_encounters = self.monster_planner.generate_encounters(
            room_count=room_counts["monsters"],
            guidelines=guidelines,
            options=options,
            rooms_with_monsters=rooms_with_monsters,
        )

        # Generate boss encounter if there's a boss room
        boss_encounter = None
        boss_room = self._find_boss_room(layout)
        if boss_room:
            boss_room_area = boss_room.width * boss_room.height
            boss_encounter = self.boss_planner.generate_boss(
                room_area=boss_room_area,
                dungeon_name=dungeon_name,
                guidelines=guidelines,
                options=options,
            )
            # Add boss encounter to the monster encounters
            monster_encounters["boss"].append(boss_encounter)

        # Generate trap themes based on room count and guidelines
        trap_themes = self.trap_planner.generate_trap_themes(
            room_count=room_counts["traps"], guidelines=guidelines, options=options
        )

        # Add span attributes for each generation stage
        current_span = trace.get_current_span() if trace else None
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
            total_monster_count = sum(
                len(encounter_list) for encounter_list in monster_encounters.values()
            )
            current_span.set_attribute(
                "global_planner.monster_count", total_monster_count
            )

            # Handle empty monster_encounters case
            all_monster_encounters = [
                encounter
                for encounter_list in monster_encounters.values()
                for encounter in encounter_list
            ]
            if all_monster_encounters:
                current_span.set_attribute(
                    "global_planner.monster_cr_range",
                    f"{min(e.get('challenge_rating', 0) for e in all_monster_encounters)}-{max(e.get('challenge_rating', 0) for e in all_monster_encounters)}",
                )
            else:
                current_span.set_attribute("global_planner.monster_cr_range", "N/A")

            current_span.set_attribute(
                "global_planner.monster_difficulty_distribution",
                str(
                    [
                        e.get("encounter_difficulty", "unknown")
                        for e in all_monster_encounters[:5]
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
            boss=boss_encounter,
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

    def _find_boss_room(self, layout: DungeonLayout):
        """Find the boss room in the layout."""
        for room in layout.rooms:
            if room.is_boss_room:
                return room
        return None
