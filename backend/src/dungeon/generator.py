"""
Main dungeon generation orchestrator.
"""

from models.dungeon import (
    DungeonGuidelines,
    DungeonLayout,
    DungeonResult,
    GenerationOptions,
    Room,
)
from utils import simple_trace

from .generators import LineGraphLayoutGenerator, LLMContentGenerator, PostProcessor


class DungeonGenerator:
    """Main orchestrator for dungeon generation."""

    def __init__(self):
        """Initialize the dungeon generator with all components."""
        self.layout_generator = LineGraphLayoutGenerator()
        self.content_generator = LLMContentGenerator()
        self.post_processor = PostProcessor()

    @simple_trace("DungeonGenerator.generate_dungeon")
    def generate_dungeon(
        self, guidelines: DungeonGuidelines, options: GenerationOptions | None = None
    ) -> DungeonResult:
        """
        Generate a complete dungeon using the full pipeline.

        Args:
            guidelines: Structured guidelines for generation
            options: Optional generation options (uses defaults if None)

        Returns:
            Complete dungeon generation result
        """
        if options is None:
            options = GenerationOptions()

        errors = []

        try:
            # Step 1: Generate basic layout
            layout = self.layout_generator.generate_layout(guidelines)

            # Step 2: Generate room dimensions using LLM
            dimension_data = self.content_generator.generate_room_dimensions(
                layout, guidelines, options
            )

            # Step 3: Apply dimensions to rooms
            layout = self._apply_dimensions_to_layout(layout, dimension_data)

            # Step 4: Generate room contents using LLM
            if options.include_contents:
                room_contents = self.content_generator.generate_room_contents(
                    layout, guidelines, options
                )
                layout = self._apply_contents_to_layout(layout, room_contents)

            # Step 5: Post-processing
            layout = self.post_processor.process(layout, guidelines, options)

            # Step 6: Validation
            validation_errors = self.post_processor.validate_layout(layout)
            errors.extend(validation_errors)

            return DungeonResult(
                dungeon=layout, guidelines=guidelines, options=options, errors=errors
            )

        except Exception as e:
            errors.append(f"Generation failed: {str(e)}")
            return DungeonResult(
                dungeon=DungeonLayout(),
                guidelines=guidelines,
                options=options,
                status="error",
                errors=errors,
            )

    def generate_layout_only(self, guidelines: DungeonGuidelines) -> DungeonLayout:
        """
        Generate only the basic layout without LLM content.

        Args:
            guidelines: Structured guidelines for generation

        Returns:
            Basic dungeon layout
        """
        return self.layout_generator.generate_layout(guidelines)

    def generate_room_dimensions(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions | None = None,
    ) -> dict:
        """
        Generate room dimensions for an existing layout.

        Args:
            layout: Existing dungeon layout
            guidelines: Generation guidelines
            options: Optional generation options

        Returns:
            Dictionary mapping room_id to dimension data
        """
        if options is None:
            options = GenerationOptions()

        return self.content_generator.generate_room_dimensions(
            layout, guidelines, options
        )

    def generate_room_contents(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions | None = None,
    ) -> list:
        """
        Generate room contents for an existing layout.

        Args:
            layout: Existing dungeon layout
            guidelines: Generation guidelines
            options: Optional generation options

        Returns:
            List of RoomContent objects
        """
        if options is None:
            options = GenerationOptions()

        return self.content_generator.generate_room_contents(
            layout, guidelines, options
        )

    def is_configured(self) -> bool:
        """Check if all components are properly configured."""
        return self.content_generator.is_configured()

    def _apply_dimensions_to_layout(
        self, layout: DungeonLayout, dimension_data: dict
    ) -> DungeonLayout:
        """Apply LLM-generated dimensions to the layout."""
        updated_rooms = []

        for room in layout.rooms:
            if room.id in dimension_data:
                data = dimension_data[room.id]
                updated_room = Room(
                    id=room.id,
                    name=data.get("name", room.name),
                    description=data.get("description", room.description),
                    anchor=room.anchor,
                    width=data.get("width", room.width),
                    height=data.get("height", room.height),
                    shape=room.shape,
                )
                updated_rooms.append(updated_room)
            else:
                updated_rooms.append(room)

        return DungeonLayout(
            rooms=updated_rooms,
            connections=layout.connections,
            metadata=layout.metadata,
        )

    def _apply_contents_to_layout(
        self, layout: DungeonLayout, room_contents: list
    ) -> DungeonLayout:
        """Apply LLM-generated contents to the layout."""
        # For now, we'll store contents in metadata
        # In the future, we might want to extend the Room class
        content_map = {content.room_id: content for content in room_contents}

        metadata = layout.metadata.copy()
        metadata["room_contents"] = content_map

        return DungeonLayout(
            rooms=layout.rooms, connections=layout.connections, metadata=metadata
        )
