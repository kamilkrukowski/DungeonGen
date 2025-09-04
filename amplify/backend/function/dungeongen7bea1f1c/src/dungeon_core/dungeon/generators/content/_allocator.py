"""
Content allocation for dungeon generation.
"""

from typing import Any

try:
    from opentelemetry import trace
except ImportError:
    trace = None

from models.dungeon import DungeonLayout, Room
from utils import simple_trace


class ContentAllocator:
    """
    Allocates globally planned content to individual rooms.

    This class takes the output from GlobalPlanner and distributes
    treasures, monsters, and traps to rooms based on their content flags.
    """

    def __init__(self):
        """Initialize the content allocator."""
        pass

    @simple_trace("ContentAllocator.allocate_content")
    def allocate_content(
        self,
        layout: DungeonLayout,
        content_plan: Any,  # DungeonContentPlan from global planner
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Allocate content from the global plan to individual rooms.

        Args:
            layout: Dungeon layout with rooms and content flags
            content_plan: Complete content plan from GlobalPlanner

        Returns:
            Dictionary mapping room IDs to their allocated content
        """
        # Create a copy of the content lists to avoid modifying the original
        treasures = content_plan.treasures.copy()
        # Deep copy the monsters dictionary to avoid modifying the original
        monsters = {
            category: encounters.copy()
            for category, encounters in content_plan.monsters.items()
        }
        traps = content_plan.traps.copy()

        # Initialize allocation results
        room_allocations = {}

        # Allocate content to each room based on content flags
        for room in layout.rooms:
            room_content = self._allocate_room_content(room, treasures, monsters, traps)
            room_allocations[room.id] = room_content

        # Add span attributes for allocation results
        current_span = trace.get_current_span() if trace else None
        if current_span:
            current_span.set_attribute(
                "content_allocator.total_rooms", len(layout.rooms)
            )
            current_span.set_attribute(
                "content_allocator.rooms_with_treasure",
                sum(1 for room in layout.rooms if room.has_treasure),
            )
            current_span.set_attribute(
                "content_allocator.rooms_with_monsters",
                sum(1 for room in layout.rooms if room.has_monsters),
            )
            current_span.set_attribute(
                "content_allocator.rooms_with_traps",
                sum(1 for room in layout.rooms if room.has_traps),
            )
            current_span.set_attribute(
                "content_allocator.treasures_allocated",
                sum(
                    len(room_content.get("treasures", []))
                    for room_content in room_allocations.values()
                ),
            )
            current_span.set_attribute(
                "content_allocator.monsters_allocated",
                sum(
                    len(room_content.get("monsters", []))
                    for room_content in room_allocations.values()
                ),
            )
            current_span.set_attribute(
                "content_allocator.traps_allocated",
                sum(
                    len(room_content.get("traps", []))
                    for room_content in room_allocations.values()
                ),
            )

        return room_allocations

    def _allocate_room_content(
        self,
        room: Room,
        treasures: list[dict[str, Any]],
        monsters: dict[str, list[dict[str, Any]]],
        traps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Allocate content for a specific room."""
        room_content = {
            "treasures": [],
            "monsters": [],
            "traps": [],
            "room_id": room.id,
        }

        # Allocate treasures if room needs them
        if room.has_treasure and treasures:
            allocated_treasure = treasures.pop(0)  # Take first available treasure
            room_content["treasures"].append(allocated_treasure)

        # Allocate monsters if room needs them
        if room.has_monsters and monsters:
            # Determine room size category
            room_size_category = self._get_room_size_category(room)

            # For boss rooms, only allocate from boss category
            if room.is_boss_room:
                if "boss" in monsters and monsters["boss"]:
                    allocated_monster = monsters["boss"].pop(0)
                    room_content["monsters"].append(allocated_monster)
            else:
                # For non-boss rooms, allocate from appropriate size category
                if room_size_category in monsters and monsters[room_size_category]:
                    allocated_monster = monsters[room_size_category].pop(0)
                    room_content["monsters"].append(allocated_monster)

        # Allocate traps if room needs them
        if room.has_traps and traps:
            allocated_trap = traps.pop(0)  # Take first available trap
            room_content["traps"].append(allocated_trap)

        return room_content

    def _get_room_size_category(self, room: Room) -> str:
        """Determine room size category based on room dimensions."""
        room_area = room.width * room.height

        # Use consistent categorization with the monster planner
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

    def validate_allocation(
        self,
        layout: DungeonLayout,
        content_plan: Any,
        room_allocations: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """
        Validate that content allocation is complete and correct.

        Args:
            layout: Dungeon layout
            content_plan: Original content plan
            room_allocations: Allocated content per room

        Returns:
            Validation results
        """
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "allocation_stats": {},
        }

        # Check if all content was allocated
        total_treasures_allocated = sum(
            len(room_content.get("treasures", []))
            for room_content in room_allocations.values()
        )
        total_monsters_allocated = sum(
            len(room_content.get("monsters", []))
            for room_content in room_allocations.values()
        )
        total_traps_allocated = sum(
            len(room_content.get("traps", []))
            for room_content in room_allocations.values()
        )

        # Check for unallocated content
        if total_treasures_allocated < len(content_plan.treasures):
            validation_results["warnings"].append(
                f"Not all treasures allocated: {total_treasures_allocated}/{len(content_plan.treasures)}"
            )

        if total_monsters_allocated < len(content_plan.monsters):
            validation_results["warnings"].append(
                f"Not all monsters allocated: {total_monsters_allocated}/{len(content_plan.monsters)}"
            )

        if total_traps_allocated < len(content_plan.traps):
            validation_results["warnings"].append(
                f"Not all traps allocated: {total_traps_allocated}/{len(content_plan.traps)}"
            )

        # Check for rooms that should have content but don't
        for room in layout.rooms:
            room_content = room_allocations.get(room.id, {})

            if room.has_treasure and not room_content.get("treasures"):
                validation_results["errors"].append(
                    f"Room {room.id} marked for treasure but none allocated"
                )

            if room.has_monsters and not room_content.get("monsters"):
                validation_results["errors"].append(
                    f"Room {room.id} marked for monsters but none allocated"
                )

            if room.has_traps and not room_content.get("traps"):
                validation_results["errors"].append(
                    f"Room {room.id} marked for traps but none allocated"
                )

        # Check for over-allocation
        for room in layout.rooms:
            room_content = room_allocations.get(room.id, {})

            if not room.has_treasure and room_content.get("treasures"):
                validation_results["warnings"].append(
                    f"Room {room.id} allocated treasure but not marked for it"
                )

            if not room.has_monsters and room_content.get("monsters"):
                validation_results["warnings"].append(
                    f"Room {room.id} allocated monsters but not marked for it"
                )

            if not room.has_traps and room_content.get("traps"):
                validation_results["warnings"].append(
                    f"Room {room.id} allocated traps but not marked for it"
                )

        # Set validation status
        if validation_results["errors"]:
            validation_results["is_valid"] = False

        # Store allocation statistics
        validation_results["allocation_stats"] = {
            "total_rooms": len(layout.rooms),
            "rooms_with_treasure": sum(1 for room in layout.rooms if room.has_treasure),
            "rooms_with_monsters": sum(1 for room in layout.rooms if room.has_monsters),
            "rooms_with_traps": sum(1 for room in layout.rooms if room.has_traps),
            "treasures_allocated": total_treasures_allocated,
            "monsters_allocated": total_monsters_allocated,
            "traps_allocated": total_traps_allocated,
        }

        return validation_results

    def get_allocation_summary(
        self, room_allocations: dict[str, list[dict[str, Any]]]
    ) -> dict[str, Any]:
        """
        Generate a summary of content allocation.

        Args:
            room_allocations: Allocated content per room

        Returns:
            Summary of allocation distribution
        """
        summary = {
            "total_rooms": len(room_allocations),
            "content_distribution": {},
            "room_details": {},
        }

        # Count content types
        treasure_count = 0
        monster_count = 0
        trap_count = 0

        for room_id, room_content in room_allocations.items():
            room_treasures = len(room_content.get("treasures", []))
            room_monsters = len(room_content.get("monsters", []))
            room_traps = len(room_content.get("traps", []))

            treasure_count += room_treasures
            monster_count += room_monsters
            trap_count += room_traps

            # Store room details
            summary["room_details"][room_id] = {
                "treasures": room_treasures,
                "monsters": room_monsters,
                "traps": room_traps,
                "total_content": room_treasures + room_monsters + room_traps,
            }

        summary["content_distribution"] = {
            "treasures": treasure_count,
            "monsters": monster_count,
            "traps": trap_count,
            "total": treasure_count + monster_count + trap_count,
        }

        return summary
