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

        Currently a stub that returns the layout unchanged.
        Future implementations could include:
        - Collision detection and resolution
        - Layout optimization
        - Balance adjustments
        - Validation checks

        Args:
            layout: The dungeon layout to process
            guidelines: Generation guidelines
            options: Generation options

        Returns:
            Processed dungeon layout
        """
        # TODO: Implement actual post-processing logic
        # For now, just return the layout unchanged
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
