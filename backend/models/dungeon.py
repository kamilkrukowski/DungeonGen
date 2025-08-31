"""
Dungeon-related data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RoomShape(Enum):
    """Supported room shapes for dungeon generation."""

    RECTANGLE = "rectangle"
    # Future: CIRCLE, POLYGON, etc.


@dataclass
class Coordinates:
    """2D coordinate system for dungeon layout."""

    x: int
    y: int

    def __add__(self, other: "Coordinates") -> "Coordinates":
        return Coordinates(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Coordinates") -> "Coordinates":
        return Coordinates(self.x - other.x, self.y - other.y)


@dataclass
class Room:
    """Represents a room in the dungeon."""

    id: str
    name: str
    description: str | None = None
    anchor: Coordinates | None = None  # Top-left anchor point
    width: int = 0
    height: int = 0
    shape: RoomShape = RoomShape.RECTANGLE

    @property
    def bounds(self) -> tuple[Coordinates, Coordinates]:
        """Returns (top_left, bottom_right) coordinates."""
        if self.anchor is None:
            raise ValueError("Room anchor not set")
        return (
            self.anchor,
            Coordinates(self.anchor.x + self.width, self.anchor.y + self.height),
        )

    @property
    def center(self) -> Coordinates:
        """Returns the center coordinates of the room."""
        if self.anchor is None:
            raise ValueError("Room anchor not set")
        return Coordinates(
            self.anchor.x + self.width // 2, self.anchor.y + self.height // 2
        )


@dataclass
class Connection:
    """Represents a connection between two rooms."""

    room_a_id: str
    room_b_id: str
    connection_type: str = "door"  # door, passage, secret, etc.
    description: str | None = None


@dataclass
class RoomContent:
    """LLM-generated content for a room."""

    room_id: str
    name: str
    description: str
    contents: list[str] = field(
        default_factory=list
    )  # furniture, items, creatures, etc.
    atmosphere: str = ""
    challenges: list[str] = field(default_factory=list)
    treasures: list[str] = field(default_factory=list)


@dataclass
class DungeonLayout:
    """Complete dungeon layout with rooms and connections."""

    rooms: list[Room] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DungeonGuidelines:
    """Structured guidelines for dungeon generation."""

    theme: str
    atmosphere: str
    difficulty: str = "medium"
    room_count: int = 5
    layout_type: str = "line_graph"
    special_requirements: list[str] = field(default_factory=list)


@dataclass
class GenerationOptions:
    """Options for dungeon generation."""

    include_contents: bool = True
    include_atmosphere: bool = True
    include_challenges: bool = True
    include_treasures: bool = True
    llm_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"


@dataclass
class DungeonResult:
    """Complete result of dungeon generation."""

    dungeon: DungeonLayout
    guidelines: DungeonGuidelines
    options: GenerationOptions
    generation_time: datetime = field(default_factory=datetime.now)
    status: str = "success"
    errors: list[str] = field(default_factory=list)
