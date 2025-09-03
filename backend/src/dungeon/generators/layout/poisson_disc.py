"""
Poisson disc sampling layout generator for sophisticated dungeon generation.
"""

import math
import random
from collections import deque
from dataclasses import dataclass

import networkx as nx
import numpy as np
from scipy.spatial import Delaunay

from models.dungeon import (
    Connection,
    Coordinates,
    DungeonGuidelines,
    DungeonLayout,
    Room,
    RoomShape,
)

from .base import BaseLayoutAlgorithm
from .hallway_sampler import HallwaySampler
from .spring_layout import SpringConfig, SpringLayout


@dataclass
class PoissonPoint:
    """Point in Poisson disc sampling."""

    x: float
    y: float
    room_size: tuple[int, int]  # (width, height)


class PoissonDiscLayoutGenerator(BaseLayoutAlgorithm):
    """
    Advanced layout generator using Poisson disc sampling for room placement.

    This generator creates organic, non-overlapping room layouts by:
    1. Sampling room sizes based on distribution
    2. Using Poisson disc sampling for room placement
    3. Creating intelligent connections between rooms
    4. Ensuring connectivity and avoiding overlaps
    """

    def __init__(self, seed: int | None = None, room_sampler=None):
        """Initialize the Poisson disc layout generator."""
        super().__init__(seed, room_sampler)

        # Poisson disc sampling parameters
        self.min_distance = 10.0  # Minimum distance between room centers
        self.max_attempts = 30  # Maximum attempts to place a room
        self.grid_size = 4.0  # Grid cell size for acceleration

    def generate_layout(self, guidelines: DungeonGuidelines) -> DungeonLayout:
        """
        Generate a dungeon layout using Poisson disc sampling.

        Args:
            guidelines: Generation guidelines

        Returns:
            DungeonLayout with rooms and connections
        """
        # Step 1: Sample room sizes
        room_sizes = self.sample_room_sizes(
            guidelines.room_count, guidelines.room_size_distribution
        )

        # Step 2: Generate room placements using Poisson disc sampling
        room_placements = self._poisson_disc_sampling(room_sizes)

        # Step 3: Create room objects
        rooms = self._create_rooms_from_placements(room_placements, guidelines)

        # Step 4: Create connections using Delaunay triangulation
        connections = self._create_smart_connections(rooms, guidelines)

        # Step 5: Apply MST pruning to get minimal spanning tree
        connections = self._apply_mst_pruning(rooms, connections)

        # Step 6: Ensure connectivity (should be guaranteed by MST)
        connections = self.ensure_connectivity(rooms, connections)

        # Step 7: Sample hallway specifications with ideal lengths
        hallway_sampler = HallwaySampler(seed=random.randint(1, 10000))
        hallway_specs = hallway_sampler.sample_hallways(rooms, connections, guidelines)

        # Step 8: Optimize layout using spring forces
        spring_config = SpringConfig(
            spring_constant=0.8,  # Reduced for better stability
            damping=0.95,  # Higher damping for convergence
            max_iterations=150,  # More iterations for better results
            convergence_threshold=0.1,
            discrete_clamp_interval=25,  # Only clamp to grid every 25 steps
            repulsion_strength=0.8,  # Moderate repulsion between rooms
            repulsion_radius=10.0,  # Repulsion starts at distance 10
            planarity_strength=1.5,  # Strong planarity enforcement
            enable_planarity=True,  # Enable planarity constraints
        )
        spring_layout = SpringLayout(spring_config)
        optimized_rooms = spring_layout.optimize_layout(rooms, hallway_specs)

        # Step 9: Generate corridor paths
        from ..postprocess import CorridorGenerator

        corridor_generator = CorridorGenerator(seed=random.randint(1, 10000))
        corridors = corridor_generator.generate_corridors(
            optimized_rooms, connections, hallway_specs
        )

        # Step 10: Get layout quality metrics
        quality_metrics = spring_layout.get_layout_quality_metrics(
            optimized_rooms, hallway_specs
        )
        hallway_stats = hallway_sampler.get_hallway_stats(hallway_specs)

        # Step 11: Center the dungeon around (0,0) for better frontend display
        centered_rooms = self._center_dungeon_rooms(optimized_rooms)

        # Step 12: Sample content flags for all rooms (if room sampler is available)
        if self.room_sampler:
            temp_layout = DungeonLayout(
                rooms=centered_rooms,
                connections=connections,
                corridors=corridors,
                metadata={},  # Minimal metadata for sampling
            )
            self.room_sampler.sample_content_flags(temp_layout, guidelines)
            # Update the centered rooms with the sampled flags
            centered_rooms = temp_layout.rooms

        # Create base layout
        base_layout = DungeonLayout(
            rooms=centered_rooms,
            connections=connections,
            corridors=corridors,
        )

        # Add metadata using the new method
        metadata = {
            "layout_type": "poisson_disc",
            "room_count": len(centered_rooms),
            "algorithm": "poisson_disc_sampling_with_spring_optimization",
            "min_distance": self.min_distance,
            "size_distribution": guidelines.room_size_distribution,
            "spring_optimization": {
                "spring_constant": spring_config.spring_constant,
                "damping": spring_config.damping,
                "max_iterations": spring_config.max_iterations,
                "convergence_threshold": spring_config.convergence_threshold,
                "discrete_clamp_interval": spring_config.discrete_clamp_interval,
                "repulsion_strength": spring_config.repulsion_strength,
                "repulsion_radius": spring_config.repulsion_radius,
                "planarity_strength": spring_config.planarity_strength,
                "enable_planarity": spring_config.enable_planarity,
            },
            "quality_metrics": quality_metrics,
            "hallway_stats": hallway_stats,
            "corridor_count": len(corridors),
        }

        return base_layout.update_values(metadata=metadata)

    def generate_corridors_for_layout(
        self, layout: "DungeonLayout", guidelines: "DungeonGuidelines"
    ) -> "DungeonLayout":
        """
        Generate corridors for an existing layout (used after post-processing).

        Args:
            layout: Existing dungeon layout
            guidelines: Dungeon guidelines

        Returns:
            Layout with corridors added
        """
        # Generate hallway specs for the existing connections
        from .hallway_sampler import HallwaySampler

        hallway_sampler = HallwaySampler(seed=random.randint(1, 10000))
        hallway_specs = hallway_sampler.sample_hallways(
            layout.rooms, layout.connections, guidelines
        )

        # Generate corridor paths
        from ..postprocess import CorridorGenerator

        corridor_generator = CorridorGenerator(seed=random.randint(1, 10000))
        corridors = corridor_generator.generate_corridors(
            layout.rooms, layout.connections, hallway_specs
        )

        # Update existing layout with corridors using the new method
        return layout.update_values(corridors=corridors)

    def _poisson_disc_sampling(
        self, room_sizes: list[tuple[int, int]]
    ) -> list[PoissonPoint]:
        """
        Generate room placements using Poisson disc sampling.

        Args:
            room_sizes: List of (width, height) tuples for each room

        Returns:
            List of PoissonPoint objects with positions and sizes
        """
        points = []
        active_points = deque()

        # Start with a central point
        first_size = room_sizes[0]
        first_point = PoissonPoint(0.0, 0.0, first_size)
        points.append(first_point)
        active_points.append(first_point)

        # Create acceleration grid
        grid_width = int(100 / self.grid_size)  # Assume 100x100 area
        grid_height = int(100 / self.grid_size)
        grid = [[None for _ in range(grid_height)] for _ in range(grid_width)]

        # Add first point to grid
        grid_x = int(first_point.x / self.grid_size)
        grid_y = int(first_point.y / self.grid_size)
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            grid[grid_x][grid_y] = first_point

        # Generate remaining points
        for i in range(1, len(room_sizes)):
            room_size = room_sizes[i]

            # Try to place the room
            point = self._try_place_room(
                room_size, points, active_points, grid, grid_width, grid_height
            )

            if point:
                points.append(point)
                active_points.append(point)

                # Add to grid
                grid_x = int(point.x / self.grid_size)
                grid_y = int(point.y / self.grid_size)
                if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                    grid[grid_x][grid_y] = point

        return points

    def _try_place_room(
        self,
        room_size: tuple[int, int],
        existing_points: list[PoissonPoint],
        active_points: deque,
        grid: list[list[PoissonPoint | None]],
        grid_width: int,
        grid_height: int,
    ) -> PoissonPoint | None:
        """
        Try to place a room using Poisson disc sampling.

        Args:
            room_size: (width, height) of the room
            existing_points: List of existing points
            active_points: Queue of active points to sample around
            grid: Acceleration grid
            grid_width: Grid width
            grid_height: Grid height

        Returns:
            PoissonPoint if successful, None otherwise
        """
        attempts = 0

        while attempts < self.max_attempts and active_points:
            # Pick a random active point
            active_point = random.choice(list(active_points))

            # Try to place new point around this active point
            for _ in range(10):  # Try 10 times around this point
                # Generate random angle and distance
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(self.min_distance, self.min_distance * 2)

                # Calculate new position
                new_x = active_point.x + distance * math.cos(angle)
                new_y = active_point.y + distance * math.sin(angle)

                # Check if position is valid
                if self._is_valid_position(
                    new_x,
                    new_y,
                    room_size,
                    existing_points,
                    grid,
                    grid_width,
                    grid_height,
                ):
                    return PoissonPoint(new_x, new_y, room_size)

            # If we couldn't place around this point, remove it from active
            active_points.remove(active_point)
            attempts += 1

        # Fallback: try random placement
        return self._fallback_placement(room_size, existing_points)

    def _is_valid_position(
        self,
        x: float,
        y: float,
        room_size: tuple[int, int],
        existing_points: list[PoissonPoint],
        grid: list[list[PoissonPoint | None]],
        grid_width: int,
        grid_height: int,
    ) -> bool:
        """
        Check if a position is valid for room placement.

        Args:
            x, y: Position to check
            room_size: Size of the room
            existing_points: List of existing points
            grid: Acceleration grid
            grid_width, grid_height: Grid dimensions

        Returns:
            True if position is valid
        """
        # Check grid cells around the point
        grid_x = int(x / self.grid_size)
        grid_y = int(y / self.grid_size)

        # Check 3x3 grid around the point
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                check_x = grid_x + dx
                check_y = grid_y + dy

                if (
                    0 <= check_x < grid_width
                    and 0 <= check_y < grid_height
                    and grid[check_x][check_y] is not None
                ):
                    existing_point = grid[check_x][check_y]
                    distance = math.sqrt(
                        (x - existing_point.x) ** 2 + (y - existing_point.y) ** 2
                    )

                    # Check if too close (considering room sizes)
                    min_required_distance = self._calculate_min_distance(
                        room_size, existing_point.room_size
                    )

                    if distance < min_required_distance:
                        return False

        return True

    def _calculate_min_distance(
        self, size1: tuple[int, int], size2: tuple[int, int]
    ) -> float:
        """
        Calculate minimum distance between two rooms based on their sizes.

        Args:
            size1: (width, height) of first room
            size2: (width, height) of second room

        Returns:
            Minimum distance between room centers
        """
        # Base minimum distance
        base_distance = self.min_distance

        # Add extra distance based on room sizes
        size1_radius = math.sqrt(size1[0] ** 2 + size1[1] ** 2) / 2
        size2_radius = math.sqrt(size2[0] ** 2 + size2[1] ** 2) / 2

        return base_distance + size1_radius + size2_radius

    def _fallback_placement(
        self, room_size: tuple[int, int], existing_points: list[PoissonPoint]
    ) -> PoissonPoint | None:
        """
        Fallback placement when Poisson disc sampling fails.

        Args:
            room_size: Size of the room
            existing_points: List of existing points

        Returns:
            PoissonPoint if successful, None otherwise
        """
        for _ in range(50):  # Try 50 random positions
            x = random.uniform(-50, 50)
            y = random.uniform(-50, 50)

            # Check distance to all existing points
            valid = True
            for existing_point in existing_points:
                distance = math.sqrt(
                    (x - existing_point.x) ** 2 + (y - existing_point.y) ** 2
                )
                min_distance = self._calculate_min_distance(
                    room_size, existing_point.room_size
                )

                if distance < min_distance:
                    valid = False
                    break

            if valid:
                return PoissonPoint(x, y, room_size)

        return None

    def _create_rooms_from_placements(
        self, placements: list[PoissonPoint], guidelines: DungeonGuidelines
    ) -> list[Room]:
        """
        Create Room objects from Poisson disc placements.

        Args:
            placements: List of PoissonPoint objects
            guidelines: Generation guidelines

        Returns:
            List of Room objects
        """
        rooms = []

        for i, placement in enumerate(placements):
            width, height = placement.room_size

            # Calculate anchor point (top-left corner)
            anchor_x = int(placement.x - width / 2)
            anchor_y = int(placement.y - height / 2)

            room = Room(
                id=f"room_{i + 1}",
                name="",  # Name will be generated by LLM based on content and theme
                anchor=Coordinates(x=anchor_x, y=anchor_y),
                width=width,
                height=height,
                shape=RoomShape.RECTANGLE,
            )
            rooms.append(room)

        return rooms

    def _create_smart_connections(
        self, rooms: list[Room], guidelines: DungeonGuidelines
    ) -> list[Connection]:
        """
        Create intelligent connections between rooms.

        Args:
            rooms: List of rooms
            guidelines: Generation guidelines

        Returns:
            List of connections
        """
        connections = []

        # Use Delaunay triangulation to create adjacency graph
        connections = self._create_delaunay_connections(rooms, guidelines)

        # Add some additional connections for variety
        additional_connections = self.create_connections(rooms, connection_density=0.1)
        connections.extend(additional_connections)

        return connections

    def _create_delaunay_connections(
        self, rooms: list[Room], guidelines: DungeonGuidelines
    ) -> list[Connection]:
        """
        Create connections using Delaunay triangulation.

        Args:
            rooms: List of rooms
            guidelines: Generation guidelines

        Returns:
            List of connections
        """
        if len(rooms) < 3:
            # Fallback for small numbers of rooms
            return self._create_fallback_connections(rooms)

        # Extract room centers for triangulation
        points = []
        room_map = {}  # Map point index to room

        for i, room in enumerate(rooms):
            if room.anchor:
                center = room.center
                points.append([center.x, center.y])
                room_map[i] = room

        if len(points) < 3:
            return self._create_fallback_connections(rooms)

        # Convert to numpy array
        points_array = np.array(points)

        try:
            # Perform Delaunay triangulation
            tri = Delaunay(points_array)

            # Create networkx graph from triangulation
            G = nx.Graph()

            # Add edges from triangulation
            for simplex in tri.simplices:
                for i in range(3):
                    for j in range(i + 1, 3):
                        room1 = room_map[simplex[i]]
                        room2 = room_map[simplex[j]]

                        # Calculate distance between room centers
                        center1 = room1.center
                        center2 = room2.center
                        distance = math.sqrt(
                            (center1.x - center2.x) ** 2 + (center1.y - center2.y) ** 2
                        )

                        # Only add connection if rooms are reasonably close
                        if distance <= 25.0:  # Maximum connection distance
                            G.add_edge(simplex[i], simplex[j], weight=distance)

            # Convert graph edges to connections
            connections = []
            connected_pairs = set()

            for edge in G.edges():
                room1 = room_map[edge[0]]
                room2 = room_map[edge[1]]

                # Create unique pair ID
                pair_id = tuple(sorted([room1.id, room2.id]))

                if pair_id not in connected_pairs:
                    connections.append(
                        Connection(
                            room_a_id=room1.id,
                            room_b_id=room2.id,
                            connection_type="door",
                            description=f"Door connecting {room1.name} to {room2.name}",
                        )
                    )
                    connected_pairs.add(pair_id)

            return connections

        except Exception as e:
            print(f"Delaunay triangulation failed: {e}, using fallback")
            return self._create_fallback_connections(rooms)

    def _create_fallback_connections(self, rooms: list[Room]) -> list[Connection]:
        """
        Create fallback connections when Delaunay triangulation fails.

        Args:
            rooms: List of rooms

        Returns:
            List of connections
        """
        connections = []
        connected_pairs = set()

        for room in rooms:
            candidates = self.find_connection_candidates(room, rooms, max_distance=20.0)

            # Connect to closest 1-2 rooms
            num_connections = random.randint(1, 2)
            for candidate_room, _ in candidates[:num_connections]:
                pair_id = tuple(sorted([room.id, candidate_room.id]))

                if pair_id not in connected_pairs:
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

    def _apply_mst_pruning(
        self, rooms: list[Room], connections: list[Connection]
    ) -> list[Connection]:
        """
        Apply Minimum Spanning Tree pruning to connections.

        This ensures we have the minimum number of connections needed
        to keep all rooms connected, removing redundant edges.

        Args:
            rooms: List of rooms
            connections: List of connections from Delaunay triangulation

        Returns:
            Pruned list of connections forming a minimal spanning tree
        """
        if len(rooms) < 2:
            return connections

        # Create graph for MST calculation
        G = nx.Graph()

        # Add all connections as weighted edges
        for connection in connections:
            room_a = next((r for r in rooms if r.id == connection.room_a_id), None)
            room_b = next((r for r in rooms if r.id == connection.room_b_id), None)

            if room_a and room_b and room_a.anchor and room_b.anchor:
                # Calculate distance as weight (shorter connections are preferred)
                distance = math.sqrt(
                    (room_a.center.x - room_b.center.x) ** 2
                    + (room_a.center.y - room_b.center.y) ** 2
                )

                G.add_edge(
                    connection.room_a_id,
                    connection.room_b_id,
                    weight=distance,
                    connection=connection,
                )

        # Calculate minimum spanning tree
        try:
            mst_edges = nx.minimum_spanning_tree(G, weight="weight")

            # Extract connections from MST
            mst_connections = []
            for edge in mst_edges.edges():
                edge_data = mst_edges.get_edge_data(edge[0], edge[1])
                if "connection" in edge_data:
                    mst_connections.append(edge_data["connection"])

            return mst_connections

        except Exception as e:
            print(f"MST calculation failed: {e}, returning original connections")
            return connections

    def _center_dungeon_rooms(self, rooms: list[Room]) -> list[Room]:
        """
        Center all rooms around (0,0) for better frontend display.

        Args:
            rooms: List of rooms to center

        Returns:
            List of centered rooms
        """
        if not rooms:
            return rooms

        # Calculate current dungeon bounds
        rooms_with_anchors = [room for room in rooms if room.anchor]
        if not rooms_with_anchors:
            return rooms

        min_x = min(room.anchor.x for room in rooms_with_anchors)
        max_x = max(room.anchor.x + room.width for room in rooms_with_anchors)
        min_y = min(room.anchor.y for room in rooms_with_anchors)
        max_y = max(room.anchor.y + room.height for room in rooms_with_anchors)

        # Calculate current dungeon center
        current_center_x = (min_x + max_x) / 2
        current_center_y = (min_y + max_y) / 2

        # Calculate offset to move to (0,0)
        offset_x = -current_center_x
        offset_y = -current_center_y

        # Create new centered rooms
        centered_rooms = []
        for room in rooms:
            if room.anchor:
                new_anchor = Coordinates(
                    x=int(room.anchor.x + offset_x), y=int(room.anchor.y + offset_y)
                )

                centered_room = Room(
                    id=room.id,
                    name=room.name,
                    description=room.description,
                    anchor=new_anchor,
                    width=room.width,
                    height=room.height,
                    shape=room.shape,
                )
                centered_rooms.append(centered_room)
            else:
                centered_rooms.append(room)

        return centered_rooms

    def get_supported_layout_types(self) -> list[str]:
        """Return list of supported layout types."""
        return ["poisson_disc", "organic"]

    def update_layout_corridors(
        self, layout: DungeonLayout, guidelines: DungeonGuidelines
    ) -> DungeonLayout:
        """
        Update corridors for an existing layout using the new update methods.

        This method demonstrates how to use the new update_corridors method
        to avoid recreating the entire DungeonLayout object.

        Args:
            layout: Existing dungeon layout
            guidelines: Dungeon guidelines

        Returns:
            Updated layout with new corridors
        """
        # Generate hallway specs for the existing connections
        hallway_sampler = HallwaySampler(seed=random.randint(1, 10000))
        hallway_specs = hallway_sampler.sample_hallways(
            layout.rooms, layout.connections, guidelines
        )

        # Generate corridor paths
        from ..postprocess import CorridorGenerator

        corridor_generator = CorridorGenerator(seed=random.randint(1, 10000))
        corridors = corridor_generator.generate_corridors(
            layout.rooms, layout.connections, hallway_specs
        )

        # Update the layout with new corridors and metadata using the new method
        # This avoids recreating the entire DungeonLayout object
        corridor_metadata = {
            "corridor_count": len(corridors),
            "corridor_generation_time": "updated",
            "hallway_stats": hallway_sampler.get_hallway_stats(hallway_specs),
        }

        # Create updated metadata
        updated_metadata = layout.metadata.copy()
        updated_metadata.update(corridor_metadata)

        return layout.update_values(corridors=corridors, metadata=updated_metadata)
