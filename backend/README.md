# DungeonGen Backend

Advanced dungeon generation backend with sophisticated layout algorithms and content generation.

## Key Features

### Layout Generation
- **Poisson Disc Sampling**: Organic, non-overlapping room layouts
- **Spring Layout Optimization**: Intelligent room positioning with physics simulation
- **Smart Connections**: Delaunay triangulation for optimal room connectivity
- **Corridor Generation**: Detailed path generation between connected rooms

### Content Generation
- **LLM-Powered**: AI-generated room descriptions, names, and content
- **Thematic Consistency**: Maintains dungeon theme and atmosphere
- **Dynamic Content**: Traps, treasures, and monsters with intelligent placement

## Avoiding Layout Recreation

The `DungeonLayout` class now includes an `update_values()` method that prevents the need to recreate entire layout objects when only specific attributes change.

### Before (Problematic)
```python
# This recreates the entire object, losing other attributes
return DungeonLayout(
    name=layout.name,
    rooms=new_rooms,
    connections=layout.connections,
    corridors=layout.corridors,
    metadata=layout.metadata,
    viewport=layout.viewport,
)
```

### After (Recommended)
```python
# This preserves all existing attributes and only updates what's needed
return layout.update_values(rooms=new_rooms)
```

### Multiple Updates
```python
# Update multiple attributes at once
return layout.update_values(
    rooms=new_rooms,
    corridors=new_corridors,
    metadata=updated_metadata
)
```

### Adding Metadata
```python
# Add metadata without losing existing data
updated_metadata = layout.metadata.copy()
updated_metadata.update(new_metadata)
return layout.update_values(metadata=updated_metadata)
```

## Benefits

1. **No More Recreation**: Avoid recreating entire `DungeonLayout` objects
2. **Attribute Preservation**: All existing attributes are maintained when updating specific ones
3. **Clear Intent**: Method names clearly indicate what's being updated
4. **Efficient**: Single method call for multiple attribute updates
5. **Maintainable**: Easier to track what changes in each update

## Usage Examples

### Updating Corridors
```python
def generate_corridors_for_layout(self, layout: DungeonLayout, guidelines: DungeonGuidelines) -> DungeonLayout:
    # Generate new corridors
    corridors = self._generate_corridors(layout.rooms, layout.connections)

    # Update layout with new corridors (preserves everything else)
    return layout.update_values(corridors=corridors)
```

### Updating Rooms and Metadata
```python
def apply_contents_to_layout(self, layout: DungeonLayout, room_contents: list) -> DungeonLayout:
    # Update rooms with new content
    updated_rooms = self._update_rooms_with_content(layout.rooms, room_contents)

    # Update metadata
    updated_metadata = layout.metadata.copy()
    updated_metadata["room_contents"] = room_contents

    # Update both at once
    return layout.update_values(
        rooms=updated_rooms,
        metadata=updated_metadata
    )
```

This approach eliminates the "arms race" problem where adding new attributes to `DungeonLayout` required updating all the places where it was recreated.
