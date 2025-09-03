"""
Post-processing generators for dungeon layouts.
"""

import math
import random

from models.dungeon import (
    Connection,
    Coordinates,
    CorridorPath,
    DungeonGuidelines,
    DungeonLayout,
    GenerationOptions,
    Room,
)

from .layout.hallway_sampler import HallwaySpec, HallwayType


class PostProcessor:
    """Handles post-processing of generated dungeons."""

    def __init__(self):
        """Initialize the post-processor."""
        pass

    def process(
        self,
        layout: "DungeonLayout",
        guidelines: "DungeonGuidelines",
        options: "GenerationOptions",
    ) -> "DungeonLayout":
        """
        Apply post-processing to the dungeon layout.

        Args:
            layout: The dungeon layout to process
            guidelines: Generation guidelines
            options: Generation options

        Returns:
            Processed dungeon layout
        """
        # Apply line layout positioning if specified
        if guidelines.layout_type == "line_graph":
            layout = self._apply_line_layout(layout)

        return layout

    def _apply_line_layout(self, layout: "DungeonLayout") -> "DungeonLayout":
        """
        Arrange rooms in a horizontal line with 2 units spacing between them.

        Args:
            layout: The dungeon layout to process

        Returns:
            Layout with rooms positioned in a line
        """
        if not layout.rooms:
            return layout

        # Sort rooms by ID to ensure consistent ordering
        sorted_rooms = sorted(layout.rooms, key=lambda room: room.id)

        # Start positioning from (0, 0)
        current_x = 0

        for room in sorted_rooms:
            # Set room anchor to current position
            room.anchor = Coordinates(x=current_x, y=0)

            # Move to next position: current room width + 2 units spacing
            current_x += room.width + 2

        return layout

    def validate_layout(self, layout: "DungeonLayout") -> list[str]:
        """
        Validate the dungeon layout and return any issues.

        Args:
            layout: The dungeon layout to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for basic issues
        if not layout.rooms:
            errors.append("No rooms in dungeon layout")

        # Check for orphaned connections
        room_ids = {room.id for room in layout.rooms}
        for connection in layout.connections:
            if connection.room_a_id not in room_ids:
                errors.append(
                    f"Connection references non-existent room: {connection.room_a_id}"
                )
            if connection.room_b_id not in room_ids:
                errors.append(
                    f"Connection references non-existent room: {connection.room_b_id}"
                )

        return errors


class CorridorGenerator:
    """
    Generates actual corridor paths between connected rooms.

    This class takes the abstract connections and hallway specifications
    and creates concrete corridor paths that can be rendered.
    """

    def __init__(self, seed: int | None = None):
        """Initialize the corridor generator."""
        if seed is not None:
            random.seed(seed)

    def generate_corridors(
        self,
        rooms: list[Room],
        connections: list[Connection],
        hallway_specs: list[HallwaySpec],
    ) -> list[CorridorPath]:
        """
        Generate corridor paths for all connections.

        Args:
            rooms: List of rooms in the dungeon
            connections: List of connections between rooms
            hallway_specs: List of hallway specifications

        Returns:
            List of CorridorPath objects
        """
        # Create lookup dictionaries
        room_lookup = {room.id: room for room in rooms}
        connection_lookup = {
            conn.room_a_id + ":" + conn.room_b_id: conn for conn in connections
        }
        connection_lookup.update(
            {conn.room_b_id + ":" + conn.room_a_id: conn for conn in connections}
        )

        corridors = []

        for spec in hallway_specs:
            # Find the connection for this hallway spec
            key_a = f"{spec.room_a.id}:{spec.room_b.id}"
            key_b = f"{spec.room_b.id}:{spec.room_a.id}"

            connection = connection_lookup.get(key_a) or connection_lookup.get(key_b)
            if not connection:
                continue

            # Generate corridor path
            corridor = self._generate_single_corridor(spec, connection, room_lookup)
            if corridor:
                corridors.append(corridor)

        return corridors

    def _generate_single_corridor(
        self, spec: HallwaySpec, connection: Connection, room_lookup: dict
    ) -> CorridorPath | None:
        """Generate a single corridor path between two rooms."""
        room_a = spec.room_a
        room_b = spec.room_b

        if not room_a.anchor or not room_b.anchor:
            return None

        # Get room centers
        center_a = room_a.center
        center_b = room_b.center

        # Generate path points
        path_points = self._generate_path_points(center_a, center_b, spec)

        # Create corridor path
        corridor = CorridorPath(
            connection_id=connection.room_a_id + ":" + connection.room_b_id,
            room_a_id=room_a.id,
            room_b_id=room_b.id,
            path_points=path_points,
            width=spec.width,
            hallway_type=spec.hallway_type.value,
            description=spec.description,
        )

        return corridor

    def _generate_path_points(
        self, start: Coordinates, end: Coordinates, spec: HallwaySpec
    ) -> list[Coordinates]:
        """
        Generate path points between two coordinates.

        Uses a simple L-shaped path for now, but can be enhanced with:
        - A* pathfinding around obstacles
        - Curved paths for grand hallways
        - Winding paths for secret tunnels
        """
        # For now, use a simple L-shaped path
        # This can be enhanced with more sophisticated pathfinding

        if spec.hallway_type == HallwayType.SECRET_TUNNEL:
            # Secret tunnels get more winding paths
            return self._generate_winding_path(start, end, spec)
        elif spec.hallway_type == HallwayType.GRAND_HALLWAY:
            # Grand hallways get slightly curved paths
            return self._generate_curved_path(start, end, spec)
        else:
            # Standard hallways get L-shaped paths
            return self._generate_l_shaped_path(start, end, spec)

    def _generate_l_shaped_path(
        self, start: Coordinates, end: Coordinates, spec: HallwaySpec
    ) -> list[Coordinates]:
        """Generate an L-shaped path between two points."""
        # Choose whether to go horizontal first or vertical first
        # This adds variety to the dungeon layout
        go_horizontal_first = random.choice([True, False])

        if go_horizontal_first:
            # Go horizontal first, then vertical
            corner = Coordinates(x=end.x, y=start.y)
            return [start, corner, end]
        else:
            # Go vertical first, then horizontal
            corner = Coordinates(x=start.x, y=end.y)
            return [start, corner, end]

    def _generate_winding_path(
        self, start: Coordinates, end: Coordinates, spec: HallwaySpec
    ) -> list[Coordinates]:
        """Generate a winding path for secret tunnels."""
        # Create a more complex path with multiple waypoints
        path = [start]

        # Add 2-3 intermediate waypoints for winding effect
        num_waypoints = random.randint(2, 3)

        for i in range(num_waypoints):
            # Calculate progress along the path
            progress = (i + 1) / (num_waypoints + 1)

            # Base position along the line
            base_x = start.x + (end.x - start.x) * progress
            base_y = start.y + (end.y - start.y) * progress

            # Add some randomness perpendicular to the main direction
            # Calculate perpendicular vector
            dx = end.x - start.x
            dy = end.y - start.y

            if abs(dx) > abs(dy):
                # More horizontal movement, add vertical randomness
                random_offset = random.randint(-2, 2)
                waypoint = Coordinates(x=int(base_x), y=int(base_y + random_offset))
            else:
                # More vertical movement, add horizontal randomness
                random_offset = random.randint(-2, 2)
                waypoint = Coordinates(x=int(base_x + random_offset), y=int(base_y))

            path.append(waypoint)

        path.append(end)
        return path

    def _generate_curved_path(
        self, start: Coordinates, end: Coordinates, spec: HallwaySpec
    ) -> list[Coordinates]:
        """Generate a slightly curved path for grand hallways."""
        # Create a curved path using a control point
        # For now, use a simple curve with one control point

        # Calculate midpoint
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2

        # Add slight curve by offsetting the midpoint
        # The curve direction is perpendicular to the main direction
        dx = end.x - start.x
        dy = end.y - start.y

        # Calculate perpendicular vector and normalize
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            perp_x = -dy / length
            perp_y = dx / length

            # Add curve (smaller offset for subtle effect)
            curve_strength = random.uniform(0.5, 1.5)
            control_x = mid_x + perp_x * curve_strength
            control_y = mid_y + perp_y * curve_strength

            # Create curved path with multiple points
            num_points = 5
            path = []

            for i in range(num_points + 1):
                t = i / num_points
                # Quadratic Bezier curve
                x = (
                    (1 - t) * (1 - t) * start.x
                    + 2 * (1 - t) * t * control_x
                    + t * t * end.x
                )
                y = (
                    (1 - t) * (1 - t) * start.y
                    + 2 * (1 - t) * t * control_y
                    + t * t * end.y
                )
                path.append(Coordinates(x=int(x), y=int(y)))

            return path

        # Fallback to straight line if points are too close
        return [start, end]
