"""
Abstract base classes for dungeon generation components.
"""

from abc import ABC, abstractmethod

from models.dungeon import (
    DungeonGuidelines,
    DungeonLayout,
    GenerationOptions,
    RoomContent,
)


class BaseLayoutGenerator(ABC):
    """Abstract base class for dungeon layout generators."""

    @abstractmethod
    def generate_layout(self, guidelines: DungeonGuidelines) -> DungeonLayout:
        """
        Generate a basic dungeon layout based on guidelines.

        Args:
            guidelines: Structured guidelines for generation

        Returns:
            DungeonLayout with rooms and connections
        """
        pass

    @abstractmethod
    def get_supported_layout_types(self) -> list[str]:
        """Return list of supported layout types."""
        pass


class BaseContentGenerator(ABC):
    """Abstract base class for room content generators."""

    @abstractmethod
    def generate_room_contents(
        self,
        layout: DungeonLayout,
        guidelines: DungeonGuidelines,
        options: GenerationOptions,
    ) -> list[RoomContent]:
        """
        Generate detailed room contents using LLM.

        Args:
            layout: Dungeon layout with dimensions
            guidelines: Generation guidelines
            options: Generation options

        Returns:
            List of RoomContent objects
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the generator is properly configured."""
        pass
