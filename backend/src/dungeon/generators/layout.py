"""
Layout generators for dungeon creation.
"""

from models.dungeon import (
    Connection,
    Coordinates,
    DungeonGuidelines,
    DungeonLayout,
    Room,
    RoomShape,
)

from .base import BaseLayoutGenerator


class LineGraphLayoutGenerator(BaseLayoutGenerator):
    """Generates a simple line-graph dungeon layout."""

    def __init__(self, room_spacing: int = 2):
        """
        Initialize the line graph layout generator.

        Args:
            room_spacing: Minimum space between rooms
        """
        self.room_spacing = room_spacing

    def generate_layout(self, guidelines: DungeonGuidelines) -> DungeonLayout:
        """
        Generate a line-graph dungeon layout.

        Creates rooms in a horizontal line with connections between adjacent rooms.

        Args:
            guidelines: Generation guidelines

        Returns:
            DungeonLayout with rooms and connections
        """
        rooms = []
        connections = []

        # Generate rooms in a line
        for i in range(guidelines.room_count):
            room_id = f"room_{i + 1}"

            # Position rooms horizontally with spacing
            x_pos = i * (6 + self.room_spacing)  # 6 is default room width
            y_pos = 0

            room = Room(
                id=room_id,
                name=f"Room {i + 1}",
                anchor=Coordinates(x_pos, y_pos),
                width=6,  # Default width
                height=4,  # Default height
                shape=RoomShape.RECTANGLE,
            )
            rooms.append(room)

            # Create connections between adjacent rooms
            if i > 0:
                connection = Connection(
                    room_a_id=f"room_{i}",
                    room_b_id=room_id,
                    connection_type="door",
                    description=f"Door connecting Room {i} to Room {i + 1}",
                )
                connections.append(connection)

        return DungeonLayout(
            rooms=rooms,
            connections=connections,
            metadata={
                "layout_type": "line_graph",
                "room_count": guidelines.room_count,
                "room_spacing": self.room_spacing,
            },
        )

    def get_supported_layout_types(self) -> list[str]:
        """Return list of supported layout types."""
        return ["line_graph"]
