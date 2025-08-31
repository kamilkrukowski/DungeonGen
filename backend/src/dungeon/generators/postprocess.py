"""
Post-processing components for dungeon generation.
"""

from models.dungeon import DungeonGuidelines, DungeonLayout, GenerationOptions


class PostProcessor:
    """Handles post-processing of generated dungeons."""

    def __init__(self):
        """Initialize the post-processor."""
        pass

    def process(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> DungeonLayout:
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

    def _apply_line_layout(self, layout: DungeonLayout) -> DungeonLayout:
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
            from models.dungeon import Coordinates

            room.anchor = Coordinates(current_x, 0)

            # Move to next position: current room width + 2 units spacing
            current_x += room.width + 2

        return layout

    def validate_layout(self, layout: DungeonLayout) -> list[str]:
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
