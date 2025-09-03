#!/usr/bin/env python3
"""
Test the corridor generation fix.
"""

import sys

sys.path.insert(0, "src")

from dungeon.generators.layout.poisson_disc import PoissonDiscLayoutGenerator

from models.dungeon import DungeonGuidelines


def test_corridor_fix():
    """Test that corridors are generated correctly after post-processing."""

    # Create guidelines
    guidelines = DungeonGuidelines(
        theme="test",
        atmosphere="mysterious",
        room_count=3,
        layout_type="poisson_disc",  # Use poisson_disc to avoid post-processing
    )

    print("Testing corridor generation fix...")
    print(
        f"Guidelines: {guidelines.theme}, {guidelines.atmosphere}, {guidelines.room_count} rooms"
    )
    print(f"Layout type: {guidelines.layout_type}")

    # Create generator
    generator = PoissonDiscLayoutGenerator()

    try:
        # Generate layout (this should include corridors)
        result = generator.generate_layout(guidelines)

        print("\nGeneration successful!")
        print(f"Rooms: {len(result.rooms)}")
        print(f"Connections: {len(result.connections)}")
        print(f"Corridors: {len(result.corridors)}")

        if result.corridors:
            print("✅ Corridors generated successfully!")
            for i, corridor in enumerate(result.corridors):
                print(f"  Corridor {i+1}: {corridor.connection_id}")
                print(f"    - Rooms: {corridor.room_a_id} -> {corridor.room_b_id}")
                print(f"    - Type: {corridor.hallway_type}")
                print(f"    - Width: {corridor.width}")
                print(f"    - Path points: {len(corridor.path_points)}")
        else:
            print("❌ No corridors generated!")

        # Now test the new method that generates corridors for existing layouts
        print("\nTesting generate_corridors_for_layout method...")

        # Create a simple layout without corridors
        from models.dungeon import Connection, Coordinates, DungeonLayout, Room

        simple_rooms = [
            Room(
                id="room1",
                name="Room 1",
                anchor=Coordinates(x=0, y=0),
                width=5,
                height=4,
            ),
            Room(
                id="room2",
                name="Room 2",
                anchor=Coordinates(x=10, y=0),
                width=6,
                height=5,
            ),
        ]
        simple_connections = [
            Connection(room_a_id="room1", room_b_id="room2", connection_type="door"),
        ]
        simple_layout = DungeonLayout(
            rooms=simple_rooms, connections=simple_connections
        )

        # Generate corridors for this layout
        layout_with_corridors = generator.generate_corridors_for_layout(
            simple_layout, guidelines
        )

        print(f"Simple layout corridors: {len(layout_with_corridors.corridors)}")
        if layout_with_corridors.corridors:
            print("✅ generate_corridors_for_layout works!")
            for corridor in layout_with_corridors.corridors:
                print(
                    f"  - {corridor.connection_id}: {len(corridor.path_points)} points"
                )
        else:
            print("❌ generate_corridors_for_layout failed!")

    except Exception as e:
        print(f"Generation failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_corridor_fix()
