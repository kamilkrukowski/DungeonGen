"""
Discrete spring layout algorithm for dungeon room positioning.
"""

import math
from dataclasses import dataclass

import numpy as np

from models.dungeon import Coordinates, Room

from .hallway_sampler import HallwaySpec


@dataclass
class SpringConfig:
    """Configuration for spring layout algorithm."""

    spring_constant: float = 0.2  # Spring stiffness
    damping: float = 0.95  # Reduced damping for better convergence
    max_iterations: int = 1000  # Maximum iterations
    convergence_threshold: float = 0.1  # Convergence threshold
    time_step: float = 0.1  # Simulation time step
    boundary_padding: float = 2.0  # Padding around room boundaries
    discrete_clamp_interval: int = 25  # Only clamp to grid every K steps
    repulsion_strength: float = 0.5  # Strength of repulsion between rooms
    repulsion_radius: float = 8.0  # Distance at which repulsion starts
    planarity_strength: float = 1.0  # Strength of planarity enforcement
    enable_planarity: bool = True  # Whether to enforce planarity


class SpringLayout:
    """
    Discrete spring layout algorithm for optimizing room positions.

    This class uses a physics-based approach where:
    - Rooms are connected by springs with ideal lengths from hallway specs
    - Spring forces pull rooms toward their ideal distances
    - Collision forces push overlapping rooms apart
    - The system converges to a stable configuration
    """

    def __init__(self, config: SpringConfig | None = None):
        """Initialize the spring layout algorithm."""
        self.config = config or SpringConfig()

    def optimize_layout(
        self, rooms: list[Room], hallway_specs: list[HallwaySpec]
    ) -> list[Room]:
        """
        Optimize room positions using spring layout.

        Args:
            rooms: List of rooms to optimize
            hallway_specs: List of hallway specifications with ideal lengths

        Returns:
            List of optimized rooms with new positions
        """
        if len(rooms) < 2:
            return rooms

        # Create room lookup and connection graph
        room_lookup = {room.id: room for room in rooms}
        connections = self._build_connection_graph(hallway_specs, room_lookup)

        # Initialize positions and velocities (ensure float64 dtype)
        positions = {
            room.id: np.array(
                [float(room.center.x), float(room.center.y)], dtype=np.float64
            )
            for room in rooms
        }
        velocities = {room.id: np.array([0.0, 0.0], dtype=np.float64) for room in rooms}

        # Run spring simulation
        for iteration in range(self.config.max_iterations):
            # Calculate forces
            forces = self._calculate_forces(positions, connections, room_lookup)

            # Apply forces and update positions
            max_displacement = 0.0

            for room_id in positions:
                if room_id in forces:
                    # Update velocity (F = ma, assume m = 1)
                    velocities[room_id] += forces[room_id] * self.config.time_step

                    # Apply damping
                    velocities[room_id] *= self.config.damping

                    # Update position
                    old_pos = positions[room_id].copy()
                    positions[room_id] += velocities[room_id] * self.config.time_step

                    # Only clamp to discrete grid every K steps for smooth movement
                    if iteration % self.config.discrete_clamp_interval == 0:
                        positions[room_id] = self._clamp_to_grid(positions[room_id])

                    # Calculate displacement
                    displacement = np.linalg.norm(positions[room_id] - old_pos)
                    max_displacement = max(max_displacement, displacement)

            # Check convergence
            if max_displacement < self.config.convergence_threshold:
                break

        # Final clamp to grid for all rooms FIRST
        for room_id in positions:
            positions[room_id] = self._clamp_to_grid(positions[room_id])

        # THEN apply no-overlap constraint on discrete positions
        self._apply_no_overlap_constraint(positions, room_lookup)

        # Update room positions
        optimized_rooms = []
        for room in rooms:
            if room.id in positions:
                new_pos = positions[room.id]
                # Calculate new anchor point (top-left corner)
                new_anchor = Coordinates(
                    x=int(new_pos[0] - room.width / 2),
                    y=int(new_pos[1] - room.height / 2),
                )

                # Create new room with updated position
                optimized_room = Room(
                    id=room.id,
                    name=room.name,
                    description=room.description,
                    anchor=new_anchor,
                    width=room.width,
                    height=room.height,
                    shape=room.shape,
                )
                optimized_rooms.append(optimized_room)
            else:
                optimized_rooms.append(room)

        return optimized_rooms

    def _build_connection_graph(
        self, hallway_specs: list[HallwaySpec], room_lookup: dict[str, Room]
    ) -> dict[str, list[tuple[str, float]]]:
        """
        Build connection graph from hallway specifications.

        Args:
            hallway_specs: List of hallway specifications
            room_lookup: Dictionary mapping room IDs to Room objects

        Returns:
            Dictionary mapping room IDs to list of (connected_room_id, ideal_length) tuples
        """
        connections = {}
        self._connection_edges = []  # Build edges list for planarity enforcement

        for spec in hallway_specs:
            room_a_id = spec.room_a.id
            room_b_id = spec.room_b.id

            # Add connection from room A to room B
            if room_a_id not in connections:
                connections[room_a_id] = []
            connections[room_a_id].append((room_b_id, spec.ideal_length))

            # Add connection from room B to room A (bidirectional)
            if room_b_id not in connections:
                connections[room_b_id] = []
            connections[room_b_id].append((room_a_id, spec.ideal_length))

            # Add edge to planarity enforcement list
            self._connection_edges.append((room_a_id, room_b_id))

        return connections

    def _clamp_to_grid(self, position: np.ndarray) -> np.ndarray:
        """
        Clamp a continuous position to the nearest grid position.

        Args:
            position: Continuous position as numpy array [x, y]

        Returns:
            Grid-clamped position
        """
        # Round to nearest integer for grid alignment
        return np.round(position).astype(np.float64)

    def _apply_no_overlap_constraint(
        self, positions: dict[str, np.ndarray], room_lookup: dict[str, Room]
    ):
        """
        Apply no-overlap constraint by pushing overlapping rooms apart.

        This method is called after each spring layout iteration to ensure
        rooms don't overlap as they move during optimization.

        Args:
            positions: Current room positions
            room_lookup: Room lookup dictionary
        """
        room_ids = list(positions.keys())
        overlap_resolved = False

        # Iterate until no overlaps remain
        max_overlap_iterations = 200  # Increased for better resolution
        for _ in range(max_overlap_iterations):
            overlap_found = False

            for i, room_a_id in enumerate(room_ids):
                for room_b_id in room_ids[i + 1 :]:
                    pos_a = positions[room_a_id]
                    pos_b = positions[room_b_id]

                    room_a = room_lookup[room_a_id]
                    room_b = room_lookup[room_b_id]

                    # Calculate room bounds
                    a_min = pos_a - np.array(
                        [float(room_a.width) / 2.0, float(room_a.height) / 2.0]
                    )
                    a_max = pos_a + np.array(
                        [float(room_a.width) / 2.0, float(room_a.height) / 2.0]
                    )
                    b_min = pos_b - np.array(
                        [float(room_b.width) / 2.0, float(room_b.height) / 2.0]
                    )
                    b_max = pos_b + np.array(
                        [float(room_b.width) / 2.0, float(room_b.height) / 2.0]
                    )

                    # Check for overlap
                    if (
                        a_min[0] < b_max[0]
                        and a_max[0] > b_min[0]
                        and a_min[1] < b_max[1]
                        and a_max[1] > b_min[1]
                    ):
                        overlap_found = True

                        # Calculate overlap amount
                        overlap_x = min(a_max[0] - b_min[0], b_max[0] - a_min[0])
                        overlap_y = min(a_max[1] - b_min[1], b_max[1] - a_min[1])

                        # Add small buffer to prevent edge cases
                        buffer = 1.0
                        overlap_x += buffer
                        overlap_y += buffer

                        # Determine push direction (push along axis with smaller overlap)
                        if overlap_x < overlap_y:
                            # Push horizontally
                            if pos_a[0] < pos_b[0]:
                                # Room A is to the left, push it further left
                                positions[room_a_id][0] -= overlap_x * 0.6
                                positions[room_b_id][0] += overlap_x * 0.4
                            else:
                                # Room A is to the right, push it further right
                                positions[room_a_id][0] += overlap_x * 0.6
                                positions[room_b_id][0] -= overlap_x * 0.4
                        else:
                            # Push vertically
                            if pos_a[1] < pos_b[1]:
                                # Room A is above, push it further up
                                positions[room_a_id][1] -= overlap_y * 0.6
                                positions[room_b_id][1] += overlap_y * 0.4
                            else:
                                # Room A is below, push it further down
                                positions[room_a_id][1] += overlap_y * 0.6
                                positions[room_b_id][1] -= overlap_y * 0.4

            if not overlap_found:
                overlap_resolved = True
                break

        if not overlap_resolved:
            print(
                f"Warning: Could not resolve all overlaps after {max_overlap_iterations} iterations"
            )
            # Force separation as last resort
            self._force_separate_overlapping_rooms(positions, room_lookup)

    def _force_separate_overlapping_rooms(
        self, positions: dict[str, np.ndarray], room_lookup: dict[str, Room]
    ):
        """
        Force separation of overlapping rooms as a last resort.
        This method aggressively separates rooms that couldn't be resolved normally.
        """
        room_ids = list(positions.keys())

        for i, room_a_id in enumerate(room_ids):
            for room_b_id in room_ids[i + 1 :]:
                pos_a = positions[room_a_id]
                pos_b = positions[room_b_id]

                room_a = room_lookup[room_a_id]
                room_b = room_lookup[room_b_id]

                # Calculate room bounds
                a_min = pos_a - np.array(
                    [float(room_a.width) / 2.0, float(room_a.height) / 2.0]
                )
                a_max = pos_a + np.array(
                    [float(room_a.width) / 2.0, float(room_a.height) / 2.0]
                )
                b_min = pos_b - np.array(
                    [float(room_b.width) / 2.0, float(room_b.height) / 2.0]
                )
                b_max = pos_b + np.array(
                    [float(room_b.width) / 2.0, float(room_b.height) / 2.0]
                )

                # Check for overlap
                if (
                    a_min[0] < b_max[0]
                    and a_max[0] > b_min[0]
                    and a_min[1] < b_max[1]
                    and a_max[1] > b_min[1]
                ):
                    # Calculate separation direction
                    separation = pos_b - pos_a
                    distance = np.linalg.norm(separation)

                    if distance > 0:
                        # Normalize and apply strong separation
                        separation_direction = separation / distance
                        force_magnitude = 5.0  # Strong force

                        # Push rooms apart aggressively
                        positions[room_a_id] -= force_magnitude * separation_direction
                        positions[room_b_id] += force_magnitude * separation_direction

    def _calculate_forces(
        self,
        positions: dict[str, np.ndarray],
        connections: dict[str, list[tuple[str, float]]],
        room_lookup: dict[str, Room],
    ) -> dict[str, np.ndarray]:
        """
        Calculate forces on all rooms.

        Args:
            positions: Current room positions
            connections: Connection graph
            room_lookup: Room lookup dictionary

        Returns:
            Dictionary mapping room IDs to force vectors
        """
        forces = {room_id: np.array([0.0, 0.0]) for room_id in positions}

        # Calculate spring forces
        for room_id, connected_rooms in connections.items():
            if room_id not in positions:
                continue

            pos_a = positions[room_id]

            for connected_id, ideal_length in connected_rooms:
                if connected_id not in positions:
                    continue

                pos_b = positions[connected_id]

                # Calculate spring force
                displacement = pos_b - pos_a
                distance = np.linalg.norm(displacement)

                if distance > 0:
                    # Spring force: F = k * (distance - ideal_length)
                    spring_force = self.config.spring_constant * (
                        distance - ideal_length
                    )
                    force_direction = displacement / distance
                    force_vector = spring_force * force_direction

                    # Apply equal and opposite forces
                    forces[room_id] += force_vector
                    forces[connected_id] -= force_vector

        # Calculate collision forces
        self._add_collision_forces(forces, positions, room_lookup)

        # Add repulsion forces between all rooms for better spacing
        self._add_repulsion_forces(forces, positions, room_lookup)

        # Add planarity enforcement forces to prevent connection crossings
        if self.config.enable_planarity:
            self._add_planarity_forces(forces, positions, room_lookup)

        # Add room-edge intersection penalties to prevent hallways through rooms
        if self.config.enable_planarity:
            self._add_room_edge_intersection_forces(forces, positions, room_lookup)

        # Add boundary forces to keep rooms within reasonable bounds
        self._add_boundary_forces(forces, positions, room_lookup)

        return forces

    def _add_collision_forces(
        self,
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """Add collision forces to prevent room overlap."""
        room_ids = list(positions.keys())

        for i, room_a_id in enumerate(room_ids):
            for room_b_id in room_ids[i + 1 :]:
                pos_a = positions[room_a_id]
                pos_b = positions[room_b_id]

                room_a = room_lookup[room_a_id]
                room_b = room_lookup[room_b_id]

                # Calculate room bounds (ensure float dtype)
                a_min = pos_a - np.array(
                    [float(room_a.width) / 2.0, float(room_a.height) / 2.0]
                )
                a_max = pos_a + np.array(
                    [float(room_a.width) / 2.0, float(room_a.height) / 2.0]
                )
                b_min = pos_b - np.array(
                    [float(room_b.width) / 2.0, float(room_b.height) / 2.0]
                )
                b_max = pos_b + np.array(
                    [float(room_b.width) / 2.0, float(room_b.height) / 2.0]
                )

                # Check for overlap
                if (
                    a_min[0] < b_max[0]
                    and a_max[0] > b_min[0]
                    and a_min[1] < b_max[1]
                    and a_max[1] > b_min[1]
                ):
                    # Calculate repulsion force
                    center_a = pos_a
                    center_b = pos_b
                    displacement = center_b - center_a
                    distance = np.linalg.norm(displacement)

                    if distance > 0:
                        # Strong repulsion force
                        repulsion_strength = 50.0 / (distance + 0.1)
                        force_direction = displacement / distance
                        force_vector = repulsion_strength * force_direction

                        forces[room_a_id] -= force_vector
                        forces[room_b_id] += force_vector

    def _add_repulsion_forces(
        self,
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """
        Add repulsion forces between all rooms to create better spacing.

        This creates a gentle push between rooms that are too close together,
        even when they're not overlapping.
        """
        room_ids = list(positions.keys())

        for i, room_a_id in enumerate(room_ids):
            for room_b_id in room_ids[i + 1 :]:
                pos_a = positions[room_a_id]
                pos_b = positions[room_b_id]

                room_a = room_lookup[room_a_id]
                room_b = room_lookup[room_b_id]

                # Calculate distance between room centers
                displacement = pos_b - pos_a
                distance = np.linalg.norm(displacement)

                # Only apply repulsion if rooms are within repulsion radius
                if distance < self.config.repulsion_radius and distance > 0:
                    # Calculate room sizes for adaptive repulsion
                    room_a_size = max(room_a.width, room_a.height) / 2.0
                    room_b_size = max(room_b.width, room_b.height) / 2.0

                    # Ideal spacing is sum of room radii plus some padding
                    ideal_spacing = room_a_size + room_b_size + 2.0

                    # Repulsion force increases as rooms get closer
                    # Use inverse square law for natural feel
                    repulsion_factor = (ideal_spacing / (distance + 0.1)) ** 2
                    repulsion_strength = (
                        self.config.repulsion_strength * repulsion_factor
                    )

                    # Apply repulsion force
                    force_direction = displacement / distance
                    force_vector = repulsion_strength * force_direction

                    # Apply equal and opposite forces
                    forces[room_a_id] -= force_vector
                    forces[room_b_id] += force_vector

    def _add_planarity_forces(
        self,
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """
        Add planarity enforcement forces to prevent connection crossings.

        This method detects when connections (edges) between rooms cross each other
        and applies forces to separate the rooms to maintain planarity.
        """
        # Check for crossings between all pairs of connections
        for i, edge1 in enumerate(self._connection_edges):
            for edge2 in self._connection_edges[i + 1 :]:
                if self._edges_cross(edge1, edge2, positions):
                    # Apply forces to separate the crossing connections
                    self._resolve_crossing(edge1, edge2, forces, positions, room_lookup)

    def _edges_cross(
        self,
        edge1: tuple[str, str],
        edge2: tuple[str, str],
        positions: dict[str, np.ndarray],
    ) -> bool:
        """
        Check if two edges cross each other.

        Args:
            edge1: Tuple of (room_a_id, room_b_id) for first connection
            edge2: Tuple of (room_a_id, room_b_id) for second connection
            positions: Current room positions

        Returns:
            True if edges cross, False otherwise
        """
        # Skip if edges share a common room
        if edge1[0] in edge2 or edge1[1] in edge2:
            return False

        # Get positions of the four rooms
        pos_a1 = positions.get(edge1[0])
        pos_b1 = positions.get(edge1[1])
        pos_a2 = positions.get(edge2[0])
        pos_b2 = positions.get(edge2[1])

        if pos_a1 is None or pos_b1 is None or pos_a2 is None or pos_b2 is None:
            return False

        # Check if line segments cross using line-line intersection
        return self._line_segments_intersect(pos_a1, pos_b1, pos_a2, pos_b2)

    def _line_segments_intersect(
        self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, p4: np.ndarray
    ) -> bool:
        """
        Check if two line segments intersect.

        Args:
            p1, p2: Endpoints of first line segment
            p3, p4: Endpoints of second line segment

        Returns:
            True if segments intersect, False otherwise
        """

        # Calculate cross products for intersection test
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        # Check if line segments intersect
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    def _resolve_crossing(
        self,
        edge1: tuple[str, str],
        edge2: tuple[str, str],
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """
        Apply forces to resolve a crossing between two connections.

        Args:
            edge1, edge2: The crossing edges
            forces: Forces dictionary to update
            positions: Current room positions
            room_lookup: Room lookup dictionary
        """
        # Calculate the midpoint of each edge
        mid1 = (positions[edge1[0]] + positions[edge1[1]]) / 2
        mid2 = (positions[edge2[0]] + positions[edge2[1]]) / 2

        # Calculate separation direction
        separation = mid2 - mid1
        distance = np.linalg.norm(separation)

        if distance > 0:
            # Normalize separation direction
            separation_direction = separation / distance

            # Apply forces to push edges apart
            force_magnitude = self.config.planarity_strength * 2.0

            # Apply forces to all four rooms involved
            for room_id in [edge1[0], edge1[1], edge2[0], edge2[1]]:
                if room_id in forces:
                    # Push rooms in the separation direction
                    forces[room_id] += force_magnitude * separation_direction

    def _add_room_edge_intersection_forces(
        self,
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """
        Add forces to prevent edges (connections) from intersecting with rooms.

        This method detects when a connection line passes through a room
        and applies forces to move the room away from the edge.
        """
        if not hasattr(self, "_connection_edges"):
            return

        # Check each edge against each room (excluding the rooms the edge connects)
        for edge in self._connection_edges:
            room_a_id, room_b_id = edge

            # Get edge endpoints
            pos_a = positions.get(room_a_id)
            pos_b = positions.get(room_b_id)

            if pos_a is None or pos_b is None:
                continue

            # Check against all other rooms
            for check_room_id, check_room in room_lookup.items():
                # Skip the rooms that this edge connects
                if check_room_id in [room_a_id, room_b_id]:
                    continue

                check_pos = positions.get(check_room_id)
                if check_pos is None:
                    continue

                # Check if edge intersects with this room
                if self._edge_intersects_room(pos_a, pos_b, check_pos, check_room):
                    # Apply force to move the room away from the edge
                    self._resolve_room_edge_intersection(
                        edge, check_room_id, forces, positions, room_lookup
                    )

    def _edge_intersects_room(
        self,
        edge_start: np.ndarray,
        edge_end: np.ndarray,
        room_center: np.ndarray,
        room: Room,
    ) -> bool:
        """
        Check if an edge intersects with a room.

        Args:
            edge_start: Start point of the edge
            edge_end: End point of the edge
            room_center: Center position of the room
            room: Room object

        Returns:
            True if edge intersects room, False otherwise
        """
        # Calculate room bounds
        room_half_width = room.width / 2.0
        room_half_height = room.height / 2.0

        room_min_x = room_center[0] - room_half_width
        room_max_x = room_center[0] + room_half_width
        room_min_y = room_center[1] - room_half_height
        room_max_y = room_center[1] + room_half_height

        # Check if edge intersects with room bounding box
        # Using line-rectangle intersection test

        # Check if either endpoint is inside the room
        if (
            room_min_x <= edge_start[0] <= room_max_x
            and room_min_y <= edge_start[1] <= room_max_y
        ):
            return True

        if (
            room_min_x <= edge_end[0] <= room_max_x
            and room_min_y <= edge_end[1] <= room_max_y
        ):
            return True

        # Check if edge crosses any of the room's edges
        # This is a simplified test - we check if the line intersects with any room boundary

        # Check horizontal boundaries
        if self._line_segments_intersect(
            edge_start,
            edge_end,
            np.array([room_min_x, room_min_y]),
            np.array([room_max_x, room_min_y]),
        ):
            return True

        if self._line_segments_intersect(
            edge_start,
            edge_end,
            np.array([room_min_x, room_max_y]),
            np.array([room_max_x, room_max_y]),
        ):
            return True

        # Check vertical boundaries
        if self._line_segments_intersect(
            edge_start,
            edge_end,
            np.array([room_min_x, room_min_y]),
            np.array([room_min_x, room_max_y]),
        ):
            return True

        if self._line_segments_intersect(
            edge_start,
            edge_end,
            np.array([room_max_x, room_min_y]),
            np.array([room_max_x, room_max_y]),
        ):
            return True

        return False

    def _resolve_room_edge_intersection(
        self,
        edge: tuple[str, str],
        room_id: str,
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """
        Apply forces to resolve a room-edge intersection.

        Args:
            edge: The edge (room_a_id, room_b_id) that intersects with a room
            room_id: ID of the room being intersected
            forces: Forces dictionary to update
            positions: Current room positions
            room_lookup: Room lookup dictionary
        """
        room_a_id, room_b_id = edge
        pos_a = positions[room_a_id]
        pos_b = positions[room_b_id]
        room_pos = positions[room_id]

        # Calculate edge midpoint
        edge_midpoint = (pos_a + pos_b) / 2

        # Calculate direction from edge to room center
        separation = room_pos - edge_midpoint
        distance = np.linalg.norm(separation)

        if distance > 0:
            # Normalize separation direction
            separation_direction = separation / distance

            # Calculate force magnitude based on planarity strength
            force_magnitude = (
                self.config.planarity_strength * 3.0
            )  # Stronger than edge-edge

            # Apply force to move the room away from the edge
            if room_id in forces:
                forces[room_id] += force_magnitude * separation_direction

            # Also apply smaller forces to the edge endpoints to help separate
            if room_a_id in forces:
                forces[room_a_id] -= force_magnitude * 0.3 * separation_direction
            if room_b_id in forces:
                forces[room_b_id] -= force_magnitude * 0.3 * separation_direction

    def _add_boundary_forces(
        self,
        forces: dict[str, np.ndarray],
        positions: dict[str, np.ndarray],
        room_lookup: dict[str, Room],
    ):
        """Add boundary forces to keep rooms within reasonable bounds."""
        if not positions:
            return

        # Calculate bounds
        all_positions = np.array(list(positions.values()))
        min_pos = np.min(all_positions, axis=0)
        max_pos = np.max(all_positions, axis=0)

        # Add padding (ensure float dtype)
        min_pos = min_pos.astype(np.float64) - self.config.boundary_padding
        max_pos = max_pos.astype(np.float64) + self.config.boundary_padding

        for room_id, position in positions.items():
            room = room_lookup[room_id]
            room_radius = float(max(room.width, room.height)) / 2.0

            # Check lower bounds
            if position[0] - room_radius < min_pos[0]:
                forces[room_id][0] += 10.0  # Push right
            if position[1] - room_radius < min_pos[1]:
                forces[room_id][1] += 10.0  # Push down

            # Check upper bounds
            if position[0] + room_radius > max_pos[0]:
                forces[room_id][0] -= 10.0  # Push left
            if position[1] + room_radius > max_pos[1]:
                forces[room_id][1] -= 10.0  # Push up

    def get_layout_quality_metrics(
        self, rooms: list[Room], hallway_specs: list[HallwaySpec]
    ) -> dict:
        """
        Calculate quality metrics for the layout.

        Args:
            rooms: List of rooms
            hallway_specs: List of hallway specifications

        Returns:
            Dictionary of quality metrics
        """
        if not rooms or not hallway_specs:
            return {}

        # Create room lookup
        room_lookup = {room.id: room for room in rooms}

        # Calculate spring energy (lower is better)
        total_spring_energy = 0.0
        total_collisions = 0

        for spec in hallway_specs:
            room_a = room_lookup.get(spec.room_a.id)
            room_b = room_lookup.get(spec.room_b.id)

            if room_a and room_b and room_a.anchor and room_b.anchor:
                center_a = room_a.center
                center_b = room_b.center

                actual_distance = math.sqrt(
                    (center_a.x - center_b.x) ** 2 + (center_a.y - center_b.y) ** 2
                )

                # Spring energy: E = 0.5 * k * (distance - ideal_length)^2
                spring_energy = (
                    0.5
                    * self.config.spring_constant
                    * (actual_distance - spec.ideal_length) ** 2
                )
                total_spring_energy += spring_energy

        # Count overlapping rooms
        for i, room_a in enumerate(rooms):
            for room_b in rooms[i + 1 :]:
                if room_a.anchor and room_b.anchor:
                    if self._rooms_overlap(room_a, room_b):
                        total_collisions += 1

        # Calculate repulsion-related metrics
        total_repulsion_energy = 0.0
        room_spacing_score = 0.0

        for i, room_a in enumerate(rooms):
            for room_b in rooms[i + 1 :]:
                if room_a.anchor and room_b.anchor:
                    center_a = room_a.center
                    center_b = room_b.center

                    distance = math.sqrt(
                        (center_a.x - center_b.x) ** 2 + (center_a.y - center_b.y) ** 2
                    )

                    # Calculate ideal spacing
                    room_a_size = max(room_a.width, room_a.height) / 2.0
                    room_b_size = max(room_b.width, room_b.height) / 2.0
                    ideal_spacing = room_a_size + room_b_size + 2.0

                    # Repulsion energy (lower is better)
                    if distance < ideal_spacing:
                        repulsion_energy = (ideal_spacing - distance) ** 2
                        total_repulsion_energy += repulsion_energy

                    # Spacing score (higher is better)
                    if distance >= ideal_spacing:
                        room_spacing_score += 1.0

        total_room_pairs = len(rooms) * (len(rooms) - 1) / 2 if len(rooms) > 1 else 0
        spacing_score = (
            room_spacing_score / total_room_pairs if total_room_pairs > 0 else 0
        )

        # Calculate planarity metrics
        total_crossings = 0
        total_room_edge_intersections = 0

        if hasattr(self, "_connection_edges"):
            # Count edge-edge crossings
            for i, edge1 in enumerate(self._connection_edges):
                for edge2 in self._connection_edges[i + 1 :]:
                    if self._edges_cross(
                        edge1,
                        edge2,
                        {
                            room.id: np.array([room.center.x, room.center.y])
                            for room in rooms
                            if room.center
                        },
                    ):
                        total_crossings += 1

            # Count room-edge intersections
            for edge in self._connection_edges:
                room_a_id, room_b_id = edge
                room_a = room_lookup.get(room_a_id)
                room_b = room_lookup.get(room_b_id)

                if room_a and room_b and room_a.anchor and room_b.anchor:
                    edge_start = np.array([room_a.center.x, room_a.center.y])
                    edge_end = np.array([room_b.center.x, room_b.center.y])

                    for check_room in rooms:
                        if (
                            check_room.id not in [room_a_id, room_b_id]
                            and check_room.anchor
                        ):
                            check_pos = np.array(
                                [check_room.center.x, check_room.center.y]
                            )
                            if self._edge_intersects_room(
                                edge_start, edge_end, check_pos, check_room
                            ):
                                total_room_edge_intersections += 1

        planarity_score = (
            1.0 - (total_crossings / len(self._connection_edges))
            if self._connection_edges
            else 1.0
        )
        room_edge_intersection_score = (
            1.0 - (total_room_edge_intersections / len(self._connection_edges))
            if self._connection_edges
            else 1.0
        )

        return {
            "total_spring_energy": total_spring_energy,
            "average_spring_energy": (
                total_spring_energy / len(hallway_specs) if hallway_specs else 0
            ),
            "total_collisions": total_collisions,
            "collision_rate": total_collisions / len(rooms) if rooms else 0,
            "total_repulsion_energy": total_repulsion_energy,
            "room_spacing_score": spacing_score,
            "total_crossings": total_crossings,
            "planarity_score": planarity_score,
            "total_room_edge_intersections": total_room_edge_intersections,
            "room_edge_intersection_score": room_edge_intersection_score,
            "layout_quality": (
                "good"
                if (
                    total_collisions == 0
                    and total_spring_energy < 100
                    and spacing_score > 0.7
                    and planarity_score > 0.8
                    and room_edge_intersection_score > 0.8
                )
                else "poor"
            ),
        }

    def _rooms_overlap(self, room_a: Room, room_b: Room) -> bool:
        """Check if two rooms overlap."""
        if not room_a.anchor or not room_b.anchor:
            return False

        a_min = room_a.anchor
        a_max = Coordinates(
            x=room_a.anchor.x + room_a.width, y=room_a.anchor.y + room_a.height
        )
        b_min = room_b.anchor
        b_max = Coordinates(
            x=room_b.anchor.x + room_b.width, y=room_b.anchor.y + room_b.height
        )

        return (
            a_min.x < b_max.x
            and a_max.x > b_min.x
            and a_min.y < b_max.y
            and a_max.y > b_min.y
        )
