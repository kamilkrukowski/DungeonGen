"""
Room sampling utilities for dimensions and content flags.
"""

import math
import random

from models.dungeon import DungeonGuidelines, DungeonLayout, Room


class RoomSampler:
    """Handles sampling of room dimensions and content flags."""

    def __init__(self):
        """Initialize the room sampler."""
        # Room size lookup table
        self.size_lookup = {
            "tiny": (3, 4),  # 12 sq units
            "small": (4, 5),  # 20 sq units
            "medium": (6, 7),  # 42 sq units
            "large": (8, 9),  # 72 sq units
            "huge": (12, 12),  # 144 sq units
        }

    def sample_room_dimensions(
        self, room_count: int, size_distribution: dict[str, float]
    ) -> list[tuple[int, int]]:
        """
        Sample room dimensions based on size distribution.
        Called EARLY in layout generation.
        """
        sizes = []

        for _ in range(room_count):
            size_category = random.choices(
                list(size_distribution.keys()), weights=list(size_distribution.values())
            )[0]

            if size_category in self.size_lookup:
                width, height = self.size_lookup[size_category]
            else:
                width, height = self.size_lookup["medium"]

            sizes.append((width, height))

        return sizes

    def sample_content_flags(
        self, layout: DungeonLayout, guidelines: DungeonGuidelines
    ) -> None:
        """
        Sample content flags for all rooms AFTER layout is generated.
        This allows intelligent placement of special rooms.
        """
        # First, determine special room assignments based on layout
        self._assign_special_room_flags(layout, guidelines)

        # Then sample regular content flags
        for room in layout.rooms:
            self._sample_room_content_flags(room, guidelines)

    def _assign_special_room_flags(
        self, layout: DungeonLayout, guidelines: DungeonGuidelines
    ) -> None:
        """Assign special room flags based on layout analysis."""
        if not layout.rooms:
            return

        # Find entrance room (most connected or strategically positioned)
        entrance_room = self._find_entrance_room(layout)
        if entrance_room:
            entrance_room.is_entrance = True

        # Find boss room (farthest from entrance, or largest, or most isolated)
        boss_room = self._find_boss_room(layout, entrance_room)
        if boss_room:
            boss_room.is_boss_room = True
            boss_room.has_monsters = True  # Boss rooms always have monsters

        # Find treasure vault (most isolated room, but not the boss room)
        treasure_vault = self._find_treasure_vault(layout, entrance_room, boss_room)
        if treasure_vault:
            treasure_vault.is_treasure_vault = True

        # Could add more special room types here:
        # - Guard room (near entrance)
        # - Secret room (hardest to reach)

    def _find_treasure_vault(
        self, layout: DungeonLayout, entrance_room: Room | None, boss_room: Room | None
    ) -> Room | None:
        """Find the best treasure vault based on layout."""
        if not layout.rooms or not entrance_room or not boss_room:
            return None

        return None
        # STUB TODO IMPLEMENT

    def _find_entrance_room(self, layout: DungeonLayout) -> Room | None:
        """Find the best entrance room based on layout."""
        if not layout.rooms:
            return None

        # Strategy 1: Room with most connections (hub)
        rooms_by_connections = sorted(
            layout.rooms,
            key=lambda r: len(
                [
                    c
                    for c in layout.connections
                    if c.room_a_id == r.id or c.room_b_id == r.id
                ]
            ),
            reverse=True,
        )

        # Combine strategies - prefer well-connected rooms on the edge
        rooms_with_centers = [r for r in layout.rooms if r.center]
        if rooms_with_centers:
            min_x = min(r.center.x for r in rooms_with_centers)
            for room in rooms_by_connections[:3]:  # Top 3 most connected
                if room.center and room.center.x <= min_x + 5:
                    return room

        # Fallback to most connected
        return rooms_by_connections[0] if rooms_by_connections else None

    def _find_boss_room(
        self, layout: DungeonLayout, entrance_room: Room | None
    ) -> Room | None:
        """Find the best boss room based on layout."""
        if not layout.rooms or not entrance_room:
            return None

        # Filter out small rooms using logarithm cutoff
        # Small/tiny rooms typically have area <= 20, so log(20) ≈ 3.0
        min_log_area = math.log(20)  # Cutoff for small rooms
        eligible_rooms = [
            room
            for room in layout.rooms
            if math.log(room.width * room.height) >= min_log_area
        ]

        if not eligible_rooms:
            # Fallback: if no medium+ rooms, use the largest available room
            eligible_rooms = layout.rooms

        # Calculate scores combining distance and size preference
        scored_rooms = []
        for room in eligible_rooms:
            score = self._calculate_boss_room_score(room, entrance_room)
            scored_rooms.append((score, room))

        # Sort by score (higher is better) and return the best room
        scored_rooms.sort(key=lambda x: x[0], reverse=True)
        return scored_rooms[0][1] if scored_rooms else None

    def _calculate_boss_room_score(self, room: Room, entrance_room: Room) -> float:
        """Calculate a score for boss room suitability."""
        score = 0.0

        # Distance component (0-1, higher is better for farther rooms)
        if entrance_room.center and room.center:
            # Calculate distance from entrance
            distance = (
                (room.center.x - entrance_room.center.x) ** 2
                + (room.center.y - entrance_room.center.y) ** 2
            ) ** 0.5

            # Normalize distance (assume max reasonable distance is 50 units)
            distance_score = min(distance / 50.0, 1.0)
            score += distance_score * 0.6  # 60% weight for distance

        # Size component using logarithm of area (0-1, higher is better for larger rooms)
        room_area = room.width * room.height
        log_area = math.log(room_area)

        # Normalize log area: min_log_area (≈3.0) to max reasonable log area (≈5.0 for area 144)
        min_log_area = math.log(20)  # Small room cutoff
        max_log_area = math.log(144)  # Huge room reference
        size_score = min((log_area - min_log_area) / (max_log_area - min_log_area), 1.0)
        size_score = max(size_score, 0.0)  # Ensure non-negative

        score += size_score * 0.4  # 40% weight for size

        return score

    def _sample_room_content_flags(
        self, room: Room, guidelines: DungeonGuidelines
    ) -> None:
        """Sample regular content flags for a room."""
        # Skip if this is a special room that should have specific content
        if room.is_boss_room:
            # Boss rooms always have monsters, often have treasure, rarely have traps
            room.has_monsters = True
            room.has_treasure = random.random() < 0.7  # 70% chance
            room.has_traps = random.random() < 0.3  # 30% chance
            return

        if room.is_entrance:
            # Entrance halls rarely have monsters, sometimes have traps, never have treasure
            room.has_monsters = random.random() < 0.1  # 10% chance
            room.has_traps = random.random() < 0.4  # 40% chance
            room.has_treasure = False
            return

        # Regular room sampling
        room.has_traps = random.random() < guidelines.percentage_rooms_trapped
        room.has_treasure = random.random() < guidelines.percentage_rooms_with_treasure
        room.has_monsters = random.random() < guidelines.percentage_rooms_with_monsters
