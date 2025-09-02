"""
Hallway sampler for assigning ideal lengths to dungeon connections.
"""

import math
import random
from dataclasses import dataclass
from enum import Enum

from models.dungeon import Connection, DungeonGuidelines, Room


class HallwayType(Enum):
    """Types of hallways/connections."""

    NARROW_PASSAGE = "narrow_passage"  # Secret, cramped
    STANDARD_DOOR = "standard_door"  # Normal room connection
    WIDE_CORRIDOR = "wide_corridor"  # Main thoroughfare
    GRAND_HALLWAY = "grand_hallway"  # Impressive, spacious
    SECRET_TUNNEL = "secret_tunnel"  # Hidden, winding


@dataclass
class HallwaySpec:
    """Specification for a hallway/connection."""

    connection: Connection
    room_a: Room
    room_b: Room
    hallway_type: HallwayType
    ideal_length: float
    width: int = 1
    description: str = ""


class HallwaySampler:
    """
    Samples hallway characteristics and assigns ideal lengths to connections.

    This class analyzes room connections and determines appropriate hallway types
    and lengths based on room sizes, connection patterns, and dungeon themes.
    """

    def __init__(self, seed: int | None = None):
        """Initialize the hallway sampler."""
        if seed is not None:
            random.seed(seed)

        # Base lengths for each hallway type
        self.base_lengths = {
            HallwayType.NARROW_PASSAGE: 3.0,
            HallwayType.STANDARD_DOOR: 5.0,
            HallwayType.WIDE_CORRIDOR: 10.0,
            HallwayType.SECRET_TUNNEL: 20.0,
        }

        # Width ranges for each hallway type
        self.width_ranges = {
            HallwayType.NARROW_PASSAGE: (1, 1),
            HallwayType.STANDARD_DOOR: (2, 3),
            HallwayType.WIDE_CORRIDOR: (2, 5),
            HallwayType.SECRET_TUNNEL: (1, 2),
        }

    def sample_hallways(
        self,
        rooms: list[Room],
        connections: list[Connection],
        guidelines: DungeonGuidelines,
    ) -> list[HallwaySpec]:
        """
        Sample hallway specifications for all connections.

        Args:
            rooms: List of rooms in the dungeon
            connections: List of connections between rooms
            guidelines: Dungeon guidelines containing hallway type distribution

        Returns:
            List of HallwaySpec objects
        """
        # Create room lookup
        room_lookup = {room.id: room for room in rooms}

        hallway_specs = []

        for connection in connections:
            room_a = room_lookup.get(connection.room_a_id)
            room_b = room_lookup.get(connection.room_b_id)

            if room_a and room_b:
                hallway_spec = self._create_hallway_spec(
                    connection, room_a, room_b, guidelines
                )
                hallway_specs.append(hallway_spec)

        return hallway_specs

    def _create_hallway_spec(
        self,
        connection: Connection,
        room_a: Room,
        room_b: Room,
        guidelines: DungeonGuidelines,
    ) -> HallwaySpec:
        """
        Create a hallway specification for a single connection.

        Args:
            connection: Connection between rooms
            room_a: First room
            room_b: Second room
            guidelines: Dungeon guidelines containing hallway type distribution

        Returns:
            HallwaySpec object
        """
        # Sample hallway type based on guidelines distribution (independent of room sizes)
        hallway_type = self._sample_hallway_type_from_guidelines(guidelines)

        # Calculate ideal length
        ideal_length = self._calculate_ideal_length(hallway_type, room_a, room_b)

        # Sample width
        width = self._sample_hallway_width(hallway_type)

        # Generate description
        description = self._generate_hallway_description(hallway_type, room_a, room_b)

        return HallwaySpec(
            connection=connection,
            room_a=room_a,
            room_b=room_b,
            hallway_type=hallway_type,
            ideal_length=ideal_length,
            width=width,
            description=description,
        )

    def _get_room_size_category(self, room: Room) -> str:
        """Determine the size category of a room."""
        area = room.width * room.height

        if area <= 12:  # 3x4 or smaller
            return "tiny"
        elif area <= 20:  # 4x5 or smaller
            return "small"
        elif area <= 42:  # 6x7 or smaller
            return "medium"
        elif area <= 72:  # 8x9 or smaller
            return "large"
        else:
            return "huge"

    def _calculate_ideal_length(
        self, hallway_type: HallwayType, room_a: Room, room_b: Room
    ) -> float:
        """Calculate ideal length for a hallway."""
        base_length = self.base_lengths[hallway_type]

        # Add variation based on room sizes
        size_factor = self._calculate_size_factor(room_a, room_b)

        # Add room dimension contribution: (width + height) / 2 for each room
        room_a_contribution = (room_a.width + room_a.height) / 2.0
        room_b_contribution = (room_b.width + room_b.height) / 2.0

        # Apply variation only to base length, with minimum of 1.0
        varied_base_length = base_length * max(1.0, random.uniform(0.8, 1.2))

        # Calculate total length and round up to ensure minimum length
        total_length = (
            varied_base_length + room_a_contribution + room_b_contribution
        ) * size_factor
        return math.ceil(total_length)

    def _sample_hallway_type_from_guidelines(
        self, guidelines: DungeonGuidelines
    ) -> HallwayType:
        """
        Sample hallway type based on guidelines distribution.

        Args:
            guidelines: Dungeon guidelines with hallway type distribution

        Returns:
            Sampled HallwayType
        """
        # Get hallway type distribution from guidelines
        distribution = guidelines.hallway_type_distribution

        # Convert string keys to HallwayType enum values
        type_mapping = {
            "narrow_passage": HallwayType.NARROW_PASSAGE,
            "standard_door": HallwayType.STANDARD_DOOR,
            "wide_corridor": HallwayType.WIDE_CORRIDOR,
            "grand_hallway": HallwayType.GRAND_HALLWAY,
            "secret_tunnel": HallwayType.SECRET_TUNNEL,
        }

        # Filter to only include types that exist in the distribution
        available_types = []
        available_weights = []

        for type_str, weight in distribution.items():
            if type_str in type_mapping and weight > 0:
                available_types.append(type_mapping[type_str])
                available_weights.append(weight)

        if not available_types:
            # Fallback to standard door if no valid types
            return HallwayType.STANDARD_DOOR

        # Sample based on weights
        return random.choices(available_types, weights=available_weights)[0]

    def _calculate_size_factor(self, room_a: Room, room_b: Room) -> float:
        """Calculate size factor based on room dimensions."""
        # Average room dimensions
        avg_width = (room_a.width + room_b.width) / 2
        avg_height = (room_a.height + room_b.height) / 2

        # Larger rooms get longer hallways
        size_factor = (avg_width + avg_height) / 20.0  # Normalize around medium size

        return max(0.5, min(2.0, size_factor))  # Clamp between 0.5 and 2.0

    def _sample_hallway_width(self, hallway_type: HallwayType) -> int:
        """Sample hallway width based on type."""
        min_width, max_width = self.width_ranges[hallway_type]
        return random.randint(min_width, max_width)

    def _generate_hallway_description(
        self, hallway_type: HallwayType, room_a: Room, room_b: Room
    ) -> str:
        """Generate a description for the hallway."""
        descriptions = {
            HallwayType.NARROW_PASSAGE: [
                f"A cramped passage connecting {room_a.name} to {room_b.name}",
                f"A narrow tunnel between {room_a.name} and {room_b.name}",
                f"A tight corridor linking {room_a.name} with {room_b.name}",
            ],
            HallwayType.STANDARD_DOOR: [
                f"A wooden door connects {room_a.name} to {room_b.name}",
                f"A stone doorway links {room_a.name} with {room_b.name}",
                f"A metal door joins {room_a.name} and {room_b.name}",
            ],
            HallwayType.WIDE_CORRIDOR: [
                f"A spacious corridor runs between {room_a.name} and {room_b.name}",
                f"A wide hallway connects {room_a.name} to {room_b.name}",
                f"A broad passage links {room_a.name} with {room_b.name}",
            ],
            HallwayType.GRAND_HALLWAY: [
                f"A magnificent hallway spans from {room_a.name} to {room_b.name}",
                f"A grand corridor connects {room_a.name} with {room_b.name}",
                f"An impressive passage joins {room_a.name} and {room_b.name}",
            ],
            HallwayType.SECRET_TUNNEL: [
                f"A hidden tunnel secretly connects {room_a.name} to {room_b.name}",
                f"A concealed passage links {room_a.name} with {room_b.name}",
                f"A secret corridor joins {room_a.name} and {room_b.name}",
            ],
        }

        if hallway_type in descriptions:
            return random.choice(descriptions[hallway_type])
        else:
            return f"A passage connects {room_a.name} to {room_b.name}"

    def get_hallway_stats(self, hallway_specs: list[HallwaySpec]) -> dict:
        """Get statistics about the hallway specifications."""
        if not hallway_specs:
            return {}

        total_hallways = len(hallway_specs)
        type_counts = {}
        total_length = 0.0
        total_width = 0

        for spec in hallway_specs:
            # Count types
            hall_type = spec.hallway_type.value
            type_counts[hall_type] = type_counts.get(hall_type, 0) + 1

            # Sum lengths and widths
            total_length += spec.ideal_length
            total_width += spec.width

        return {
            "total_hallways": total_hallways,
            "type_distribution": type_counts,
            "average_length": total_length / total_hallways,
            "average_width": total_width / total_hallways,
            "total_length": total_length,
        }
