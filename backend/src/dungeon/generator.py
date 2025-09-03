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

from .generators import LLMContentGenerator, PoissonDiscLayoutGenerator, PostProcessor


class DungeonGenerator:
    """Main orchestrator for dungeon generation."""

    def __init__(self):
        """Initialize the dungeon generator with all components."""
        self.layout_generator = PoissonDiscLayoutGenerator()
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

            # Step 2: Generate room contents using LLM (content flags are set during layout generation)
            if options.include_contents:
                room_contents = self.content_generator.generate_room_contents(
                    layout, guidelines, options
                )
                layout = self._apply_contents_to_layout(layout, room_contents)

            # Step 3: Post-processing
            layout = self.post_processor.process(layout, guidelines, options)

            # Step 4: Generate corridors (after post-processing to ensure final room positions)
            if hasattr(self.layout_generator, "generate_corridors_for_layout"):
                layout = self.layout_generator.generate_corridors_for_layout(
                    layout, guidelines
                )

            # Step 5: Validation
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

    def _apply_contents_to_layout(
        self, layout: DungeonLayout, room_contents: list
    ) -> DungeonLayout:
        """Apply LLM-generated contents to the layout."""
        print(
            f"DEBUG: _apply_contents_to_layout called with {len(room_contents)} room contents"
        )

        # Create content map for metadata
        content_map = {content.room_id: content for content in room_contents}
        print(f"DEBUG: Created content map with keys: {list(content_map.keys())}")

        # Update room objects with new names and descriptions
        updated_rooms = []
        for room in layout.rooms:
            if room.id in content_map:
                content = content_map[room.id]
                updated_room = Room(
                    id=room.id,
                    name=content.name,  # Use the LLM-generated name
                    description=content.player_description,  # Use the LLM-generated player description
                    anchor=room.anchor,
                    width=room.width,
                    height=room.height,
                    shape=room.shape,
                    has_traps=bool(content.traps and len(content.traps) > 0),
                    has_treasure=bool(content.treasures and len(content.treasures) > 0),
                    has_monsters=bool(content.monsters and len(content.monsters) > 0),
                )
                updated_rooms.append(updated_room)
                print(f"DEBUG: Updated room {room.id} with content")
            else:
                updated_rooms.append(room)
                print(f"DEBUG: Room {room.id} has no content")

        # Ensure metadata is properly initialized
        metadata = layout.metadata.copy() if layout.metadata else {}
        metadata["room_contents"] = content_map
        print(f"DEBUG: Final metadata keys: {list(metadata.keys())}")

        return DungeonLayout(
            rooms=updated_rooms, connections=layout.connections, metadata=metadata
        )
