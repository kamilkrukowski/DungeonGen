"""
Content allocation for dungeon generation.
"""

from typing import Any

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
        monsters = content_plan.monsters.copy()
        traps = content_plan.traps.copy()

        # Initialize allocation results
        room_allocations = {}

        # Allocate content to each room based on content flags
        for room in layout.rooms:
            room_content = self._allocate_room_content(room, treasures, monsters, traps)
            room_allocations[room.id] = room_content

        return room_allocations

    def _allocate_room_content(
        self,
        room: Room,
        treasures: list[dict[str, Any]],
        monsters: list[dict[str, Any]],
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
            allocated_monster = monsters.pop(0)  # Take first available monster
            room_content["monsters"].append(allocated_monster)

        # Allocate traps if room needs them
        if room.has_traps and traps:
            allocated_trap = traps.pop(0)  # Take first available trap
            room_content["traps"].append(allocated_trap)

        return room_content

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
