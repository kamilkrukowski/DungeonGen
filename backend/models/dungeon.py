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
class CanvasViewport:
    """Canvas viewport dimensions for automatic grid fitting."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int
    margin: int = 5  # Default margin around the dungeon

    @property
    def width(self) -> int:
        """Viewport width in grid units."""
        return self.max_x - self.min_x

    @property
    def height(self) -> int:
        """Viewport height in grid units."""
        return self.max_y - self.min_y

    @property
    def center(self) -> Coordinates:
        """Center point of the viewport."""
        return Coordinates(
            (self.min_x + self.max_x) // 2, (self.min_y + self.max_y) // 2
        )

    @classmethod
    def from_rooms(cls, rooms: list["Room"], margin: int = 5) -> "CanvasViewport":
        """Create viewport from a list of rooms."""
        if not rooms:
            return cls(min_x=-10, min_y=-10, max_x=10, max_y=10, margin=margin)

        min_x = min(room.anchor.x for room in rooms if room.anchor)
        max_x = max(room.anchor.x + room.width for room in rooms if room.anchor)
        min_y = min(room.anchor.y for room in rooms if room.anchor)
        max_y = max(room.anchor.y + room.height for room in rooms if room.anchor)

        # Calculate viewport dimensions
        viewport_width = max_x - min_x + 2.0 * margin
        viewport_height = max_y - min_y + 2.0 * margin

        # Center the viewport around (0,0) for better frontend centering
        half_width = viewport_width / 2.0
        half_height = viewport_height / 2.0

        return cls(
            min_x=-half_width,
            min_y=-half_height,
            max_x=half_width,
            max_y=half_height,
            margin=margin,
        )


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

    # Content flags determined during dimension generation
    has_traps: bool = False
    has_treasure: bool = False
    has_monsters: bool = False

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

    # Content flags indicating what was sampled for this room
    has_traps: bool = False
    has_treasure: bool = False
    has_monsters: bool = False


@dataclass
class DungeonLayout:
    """Complete dungeon layout with rooms and connections."""

    rooms: list[Room] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    corridors: list["CorridorPath"] = field(default_factory=list)  # NEW: corridor paths
    metadata: dict[str, Any] = field(default_factory=dict)
    viewport: CanvasViewport | None = None

    def __post_init__(self):
        """Calculate viewport after initialization if not provided."""
        if self.viewport is None and self.rooms:
            self.viewport = CanvasViewport.from_rooms(self.rooms)


@dataclass
class CorridorPath:
    """Represents the actual path of a corridor between rooms."""

    connection_id: str  # References the Connection
    room_a_id: str
    room_b_id: str
    path_points: list[Coordinates]  # List of grid coordinates forming the path
    width: int
    hallway_type: str
    description: str | None = None


@dataclass
class DungeonGuidelines:
    """Structured guidelines for dungeon generation."""

    theme: str
    atmosphere: str
    difficulty: str = "medium"
    room_count: int = 10
    layout_type: str = "line_graph"
    special_requirements: list[str] = field(default_factory=list)

    room_size_distribution: dict[str, float] = field(
        default_factory=lambda: {
            "tiny": 0.1,
            "small": 0.35,
            "medium": 0.45,
            "large": 0.15,
            "huge": 0.05,
        }
    )

    hallway_type_distribution: dict[str, float] = field(
        default_factory=lambda: {
            "narrow_passage": 0.2,
            "standard_door": 0.5,
            "wide_corridor": 0.2,
            "secret_tunnel": 0.1,
        }
    )

    # Room content generation percentages
    percentage_rooms_trapped: float = 0.15  # 0-35% range
    percentage_rooms_with_treasure: float = 0.20  # 10-20% range
    percentage_rooms_with_monsters: float = 0.45  # 25-75% range


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
