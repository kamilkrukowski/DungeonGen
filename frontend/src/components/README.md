# Dungeon Grid Component

## Overview

The `DungeonGrid` component is a React component that renders a resizable integer grid for visualizing dungeon layouts using HTML5 Canvas. It provides panning, zooming, and room selection capabilities with smooth performance.

## Features

- **Resizable Integer Grid**: Displays a grid with faded grey lines for boundaries
- **Panning**: Click and drag to move around the grid
- **Zooming**: Mouse wheel or zoom buttons to zoom in/out
- **Room Visualization**: Renders dungeon rooms as colored rectangles
- **Room Selection**: Click on rooms to select them
- **Responsive Design**: Adapts to different screen sizes
- **HTML5 Canvas**: High-performance rendering with smooth interactions
- **Auto-Fit Viewport**: Automatically fits dungeon to canvas on load
- **Canvas Viewport**: Backend provides optimal viewing dimensions
- **Drag & Drop Ready**: Rooms are draggable (position updates to be implemented)

## Props

```jsx
<DungeonGrid
  dungeonData={parsedDungeonData}  // Parsed dungeon data from backend
  width={800}                      // Grid width (number or percentage string)
  height={600}                     // Grid height
  onRoomSelect={handleRoomSelect}  // Callback when room is selected
  selectedRoomId={selectedRoomId}  // Currently selected room ID
/>
```

## Usage

```jsx
import DungeonGrid from './components/DungeonGrid';
import { parseDungeonData } from '../models/DungeonModels';

// Parse backend response
const parsedData = parseDungeonData(backendResponse);

// Render the grid
<DungeonGrid
  dungeonData={parsedData}
  width="100%"
  height={600}
  onRoomSelect={(room) => console.log('Selected:', room.name)}
  selectedRoomId={selectedRoomId}
/>
```

## Data Structure

The component expects dungeon data in the following format (after parsing):

```javascript
{
  dungeon: {
    rooms: [
      {
        id: "room_1",
        name: "Entrance Hall",
        description: "A grand entrance hall",
        anchor: { x: 0, y: 0 },  // Grid coordinates
        width: 3,                 // Grid units
        height: 2,                // Grid units
        shape: "rectangle"
      }
    ],
    connections: [...],
    metadata: {...},
    viewport: {
      min_x: -1,                  // Minimum X coordinate
      min_y: -1,                  // Minimum Y coordinate
      max_x: 6,                   // Maximum X coordinate
      max_y: 4,                   // Maximum Y coordinate
      margin: 5                   // Margin around dungeon
    }
  },
  guidelines: {...},
  options: {...},
  generation_time: "...",
  status: "success",
  errors: []
}
```

## Controls

- **Mouse Wheel**: Zoom in/out
- **Click & Drag**: Pan around the grid
- **Click on Room**: Select a room
- **Zoom In Button**: Increase zoom level
- **Zoom Out Button**: Decrease zoom level
- **Reset View Button**: Return to default view
- **Fit to View Button**: Auto-fit dungeon to canvas

## Grid System

- Grid size: 50px per unit
- Grid color: Faded grey (#e0e0e0)
- Room colors: Rotating palette of 8 colors
- Coordinate system: Integer-based grid coordinates

## Future Enhancements

- [ ] Room position updates on drag
- [ ] Connection line visualization
- [ ] Room content tooltips
- [ ] Grid snapping for room placement
- [ ] Export functionality
- [ ] Multiple selection support
