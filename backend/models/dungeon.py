"""
Dungeon-related data models.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RoomShape(Enum):
    """Supported room shapes for dungeon generation."""

    RECTANGLE = "rectangle"
    # Future: CIRCLE, POLYGON, etc.

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class Coordinates(BaseModel):
    """2D coordinate system for dungeon layout."""

    x: int
    y: int

    model_config = ConfigDict(use_enum_values=True)

    def __add__(self, other: "Coordinates") -> "Coordinates":
        return Coordinates(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: "Coordinates") -> "Coordinates":
        return Coordinates(x=self.x - other.x, y=self.y - other.y)


class CanvasViewport(BaseModel):
    """Canvas viewport dimensions for automatic grid fitting."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int
    margin: int = Field(default=5)  # Default margin around the dungeon

    model_config = ConfigDict(use_enum_values=True)

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
            x=(self.min_x + self.max_x) // 2, y=(self.min_y + self.max_y) // 2
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


class Room(BaseModel):
    """Represents a room in the dungeon."""

    id: str
    name: str
    description: str | None = None
    anchor: Coordinates | None = None  # Top-left anchor point
    width: int = Field(default=0)
    height: int = Field(default=0)
    shape: RoomShape = Field(default=RoomShape.RECTANGLE)

    model_config = ConfigDict(use_enum_values=True)

    # Content flags determined during dimension generation
    has_traps: bool = Field(default=False)
    has_treasure: bool = Field(default=False)
    has_monsters: bool = Field(default=False)

    # Special room flags determined during layout analysis
    is_boss_room: bool = Field(default=False)
    is_entrance: bool = Field(default=False)
    is_treasure_vault: bool = Field(default=False)

    @property
    def bounds(self) -> tuple[Coordinates, Coordinates]:
        """Returns (top_left, bottom_right) coordinates."""
        if self.anchor is None:
            raise ValueError("Room anchor not set")
        return (
            self.anchor,
            Coordinates(x=self.anchor.x + self.width, y=self.anchor.y + self.height),
        )

    @property
    def center(self) -> Coordinates:
        """Returns the center coordinates of the room."""
        if self.anchor is None:
            raise ValueError("Room anchor not set")
        return Coordinates(
            x=self.anchor.x + self.width // 2, y=self.anchor.y + self.height // 2
        )


class Connection(BaseModel):
    """Represents a connection between two rooms."""

    room_a_id: str
    room_b_id: str
    connection_type: str = Field(default="door")  # door, passage, secret, etc.
    description: str | None = None


class TrapData(BaseModel):
    """Data model for traps in rooms."""

    name: str
    trigger: str
    effect: str
    difficulty: str
    location: str


class TreasureData(BaseModel):
    """Data model for treasure in rooms."""

    name: str
    description: str
    value: str
    location: str
    requirements: str


class MonsterData(BaseModel):
    """Data model for monsters in rooms."""

    name: str
    description: str
    stats: str
    behavior: str
    location: str


class RoomContent(BaseModel):
    """Content for a dungeon room."""

    room_id: str
    purpose: str
    name: str
    gm_description: str
    player_description: str
    traps: list[TrapData] | None = None
    treasures: list[TreasureData] | None = None
    monsters: list[MonsterData] | None = None


class DungeonLayout(BaseModel):
    """Complete dungeon layout with rooms and connections."""

    rooms: list[Room] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    corridors: list["CorridorPath"] = Field(default_factory=list)  # NEW: corridor paths
    metadata: dict[str, Any] = Field(default_factory=dict)
    viewport: CanvasViewport | None = None

    model_config = ConfigDict(use_enum_values=True)

    def model_post_init(self, __context: Any) -> None:
        """Calculate viewport after initialization if not provided."""
        if self.viewport is None and self.rooms:
            self.viewport = CanvasViewport.from_rooms(self.rooms)


class CorridorPath(BaseModel):
    """Represents the actual path of a corridor between rooms."""

    connection_id: str  # References the Connection
    room_a_id: str
    room_b_id: str
    path_points: list[Coordinates]  # List of grid coordinates forming the path
    width: int
    hallway_type: str
    description: str | None = None


class DungeonGuidelines(BaseModel):
    """Structured guidelines for dungeon generation."""

    theme: str
    atmosphere: str
    difficulty: str = Field(default="medium")
    room_count: int = Field(default=10)
    layout_type: str = Field(default="line_graph")
    special_requirements: list[str] = Field(default_factory=list)
    prompt: str = Field(default="")  # Custom user prompt for dungeon generation

    room_size_distribution: dict[str, float] = Field(
        default_factory=lambda: {
            "tiny": 0.1,
            "small": 0.35,
            "medium": 0.45,
            "large": 0.15,
            "huge": 0.05,
        }
    )

    hallway_type_distribution: dict[str, float] = Field(
        default_factory=lambda: {
            "narrow_passage": 0.2,
            "standard_door": 0.5,
            "wide_corridor": 0.2,
            "secret_tunnel": 0.1,
        }
    )

    # Room content generation percentages
    percentage_rooms_trapped: float = Field(default=0.15)  # 0-35% range
    percentage_rooms_with_treasure: float = Field(default=0.20)  # 10-20% range
    percentage_rooms_with_monsters: float = Field(default=0.45)  # 25-75% range


class GenerationOptions(BaseModel):
    """Options for dungeon generation."""

    include_contents: bool = Field(default=True)
    include_atmosphere: bool = Field(default=True)
    include_challenges: bool = Field(default=True)
    include_treasures: bool = Field(default=True)
    llm_model: str = Field(default="meta-llama/llama-4-scout-17b-16e-instruct")


class DungeonResult(BaseModel):
    """Complete result of dungeon generation."""

    dungeon: DungeonLayout
    guidelines: DungeonGuidelines
    options: GenerationOptions
    generation_time: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="success")
    errors: list[str] = Field(default_factory=list)
