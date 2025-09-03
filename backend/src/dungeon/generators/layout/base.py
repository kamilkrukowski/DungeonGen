"""
Base layout algorithm with common methods for advanced dungeon generation.
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.dungeon import (
    Connection,
    DungeonGuidelines,
    DungeonLayout,
    Room,
)


@dataclass
class RoomSizeTemplate:
    """Template for room size generation."""

    min_width: int
    max_width: int
    min_height: int
    max_height: int
    weight: float = 1.0


@dataclass
class PlacementConstraints:
    """Constraints for room placement."""

    min_distance: float = 8.0
    max_distance: float = 50.0
    avoid_overlap: bool = True
    connection_preference: float = 0.7  # Prefer rooms closer to existing connections


class BaseLayoutAlgorithm(ABC):
    """Base class for advanced layout algorithms."""

    def __init__(self, seed: int | None = None, room_sampler=None):
        """Initialize the layout algorithm."""
        if seed is not None:
            random.seed(seed)

        # Room size templates based on guidelines
        self.size_templates = {
            "tiny": RoomSizeTemplate(3, 4, 3, 4, 0.1),
            "small": RoomSizeTemplate(4, 7, 3, 5, 0.35),
            "medium": RoomSizeTemplate(6, 10, 4, 7, 0.45),
            "large": RoomSizeTemplate(8, 15, 5, 9, 0.15),
            "huge": RoomSizeTemplate(12, 25, 6, 12, 0.05),
        }

        self.constraints = PlacementConstraints()
        self.room_sampler = room_sampler

    @abstractmethod
    def generate_layout(self, guidelines: DungeonGuidelines) -> DungeonLayout:
        """Generate a dungeon layout based on guidelines."""
        pass

    def sample_room_sizes(
        self, room_count: int, size_distribution: dict[str, float]
    ) -> list[tuple[int, int]]:
        """
        Sample room dimensions based on size distribution.

        Args:
            room_count: Number of rooms to generate
            size_distribution: Distribution of room sizes

        Returns:
            List of (width, height) tuples
        """
        # Use room sampler if available, otherwise fall back to local implementation
        if self.room_sampler:
            return self.room_sampler.sample_room_dimensions(
                room_count, size_distribution
            )

        # Fallback to local implementation
        sizes = []

        for _ in range(room_count):
            # Sample size category based on distribution
            size_category = random.choices(
                list(size_distribution.keys()), weights=list(size_distribution.values())
            )[0]

            # Use static size lookup instead of templates
            size_lookup = self._get_room_size_lookup()
            if size_category in size_lookup:
                width, height = size_lookup[size_category]
            else:
                # Fallback to medium size
                width, height = size_lookup["medium"]

            sizes.append((width, height))

        return sizes

    def _get_room_size_lookup(self) -> dict[str, tuple[int, int]]:
        """
        Get static room size lookup table.

        Returns:
            Dictionary mapping size categories to (width, height) tuples
        """
        return {
            "tiny": (3, 4),  # 12 sq units
            "small": (4, 5),  # 20 sq units
            "medium": (6, 7),  # 42 sq units
            "large": (8, 9),  # 72 sq units
            "huge": (12, 12),  # 144 sq units
        }

    def check_collision(
        self, room: Room, existing_rooms: list[Room], margin: float = 1.0
    ) -> bool:
        """
        Check if a room collides with existing rooms.

        Args:
            room: Room to check
            existing_rooms: List of existing rooms
            margin: Minimum distance between rooms

        Returns:
            True if collision detected
        """
        if not room.anchor:
            return True

        room_bounds = room.bounds
        room_min, room_max = room_bounds

        for existing_room in existing_rooms:
            if not existing_room.anchor:
                continue

            existing_bounds = existing_room.bounds
            existing_min, existing_max = existing_bounds

            # Check for overlap with margin
            if (
                room_min.x - margin < existing_max.x
                and room_max.x + margin > existing_min.x
                and room_min.y - margin < existing_max.y
                and room_max.y + margin > existing_min.y
            ):
                return True

        return False

    def find_connection_candidates(
        self, room: Room, existing_rooms: list[Room], max_distance: float = 15.0
    ) -> list[tuple[Room, float]]:
        """
        Find rooms that could be connected to the given room.

        Args:
            room: Room to find connections for
            existing_rooms: List of existing rooms
            max_distance: Maximum distance for connections

        Returns:
            List of (room, distance) tuples sorted by distance
        """
        if not room.anchor:
            return []

        candidates = []
        room_center = room.center

        for existing_room in existing_rooms:
            if existing_room.id == room.id or not existing_room.anchor:
                continue

            existing_center = existing_room.center
            distance = math.sqrt(
                (room_center.x - existing_center.x) ** 2
                + (room_center.y - existing_center.y) ** 2
            )

            if distance <= max_distance:
                candidates.append((existing_room, distance))

        # Sort by distance
        candidates.sort(key=lambda x: x[1])
        return candidates

    def create_connections(
        self, rooms: list[Room], connection_density: float = 0.3
    ) -> list[Connection]:
        """
        Create connections between rooms based on proximity and density.

        Args:
            rooms: List of rooms to connect
            connection_density: Probability of connecting nearby rooms

        Returns:
            List of connections
        """
        connections = []
        connected_pairs = set()

        for room in rooms:
            candidates = self.find_connection_candidates(room, rooms)

            for candidate_room, distance in candidates:
                pair_id = tuple(sorted([room.id, candidate_room.id]))

                if pair_id in connected_pairs:
                    continue

                # Higher probability for closer rooms
                connection_prob = connection_density * (1.0 - distance / 15.0)

                if random.random() < connection_prob:
                    connections.append(
                        Connection(
                            room_a_id=room.id,
                            room_b_id=candidate_room.id,
                            connection_type="door",
                            description=f"Door connecting {room.name} to {candidate_room.name}",
                        )
                    )
                    connected_pairs.add(pair_id)

        return connections

    def ensure_connectivity(
        self, rooms: list[Room], connections: list[Connection]
    ) -> list[Connection]:
        """
        Ensure all rooms are connected by adding minimum spanning tree connections.

        Args:
            rooms: List of rooms
            connections: Existing connections

        Returns:
            Updated list of connections
        """
        # Create adjacency list
        adjacency = {room.id: set() for room in rooms}
        for conn in connections:
            adjacency[conn.room_a_id].add(conn.room_b_id)
            adjacency[conn.room_b_id].add(conn.room_a_id)

        # Find connected components
        visited = set()
        components = []

        for room in rooms:
            if room.id in visited:
                continue

            # BFS to find component
            component = set()
            queue = [room.id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                component.add(current)

                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)

            components.append(component)

        # If multiple components, connect them
        if len(components) > 1:
            for i in range(len(components) - 1):
                comp1 = list(components[i])
                comp2 = list(components[i + 1])

                # Find closest pair between components
                min_distance = float("inf")
                best_pair = None

                for room1_id in comp1:
                    room1 = next(r for r in rooms if r.id == room1_id)
                    for room2_id in comp2:
                        room2 = next(r for r in rooms if r.id == room2_id)

                        if room1.anchor and room2.anchor:
                            distance = math.sqrt(
                                (room1.center.x - room2.center.x) ** 2
                                + (room1.center.y - room2.center.y) ** 2
                            )

                            if distance < min_distance:
                                min_distance = distance
                                best_pair = (room1, room2)

                if best_pair:
                    room1, room2 = best_pair
                    connections.append(
                        Connection(
                            room_a_id=room1.id,
                            room_b_id=room2.id,
                            connection_type="passage",
                            description=f"Passage connecting {room1.name} to {room2.name}",
                        )
                    )

        return connections

    def get_supported_layout_types(self) -> list[str]:
        """Return list of supported layout types."""
        return ["poisson_disc", "organic", "branching"]
