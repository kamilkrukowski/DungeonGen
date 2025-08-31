# DungeonGen Backend Architecture Plan

## Overview

The dungeon generator follows a modular architecture with clear separation between API routing (`backend/api`) and business logic (`backend/src`). The system supports both full end-to-end generation and partial workflow steps.

## Data Classes

### Core Data Structures

```python
# backend/src/dungeon/models.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum

class RoomShape(Enum):
    RECTANGLE = "rectangle"
    # Future: CIRCLE, POLYGON, etc.

@dataclass
class Coordinates:
    """2D coordinate system for dungeon layout"""
    x: int
    y: int

@dataclass
class Room:
    """Represents a room in the dungeon"""
    id: str
    name: str
    description: Optional[str] = None
    anchor: Coordinates = None  # Top-left anchor point
    width: int = 0
    height: int = 0
    shape: RoomShape = RoomShape.RECTANGLE

    @property
    def bounds(self) -> Tuple[Coordinates, Coordinates]:
        """Returns (top_left, bottom_right) coordinates"""
        return (
            self.anchor,
            Coordinates(self.anchor.x + self.width, self.anchor.y + self.height)
        )

@dataclass
class Connection:
    """Represents a connection between two rooms"""
    room_a_id: str
    room_b_id: str
    connection_type: str = "door"  # door, passage, secret, etc.
    description: Optional[str] = None

@dataclass
class DungeonLayout:
    """Complete dungeon layout with rooms and connections"""
    rooms: List[Room]
    connections: List[Connection]
    metadata: Dict[str, any] = None

@dataclass
class RoomContent:
    """LLM-generated content for a room"""
    room_id: str
    name: str
    description: str
    contents: List[str]  # furniture, items, creatures, etc.
    atmosphere: str
    challenges: List[str]
    treasures: List[str]
```

## Workflow Steps

### 1. User Guidelines Processing
- **Input**: Natural language description of desired dungeon
- **Output**: Structured guidelines object
- **Endpoint**: `/api/generate/guidelines`

### 2. Initial Layout Generation
- **Input**: Guidelines object
- **Output**: Basic room layout (5 rooms in line-graph)
- **Classes**: `BaseLayoutGenerator` → `LineGraphLayoutGenerator`
- **Endpoint**: `/api/generate/layout`

### 3. Room Dimension Generation (LLM)
- **Input**: Room layout in natural text
- **Output**: Dictionary mapping room_id → {size, name, description}
- **LLM Flow**: LangChain with structured output
- **Endpoint**: `/api/generate/dimensions`

### 4. Room Content Generation (LLM)
- **Input**: Room information and guidelines
- **Output**: Detailed room contents and atmosphere
- **LLM Flow**: LangChain for immersive descriptions
- **Endpoint**: `/api/generate/contents`

### 5. Post-Processing
- **Input**: Complete dungeon data
- **Output**: Finalized dungeon with any adjustments
- **Current**: Identity function (stub)
- **Endpoint**: `/api/generate/postprocess`

## Master Endpoint Design

### `/api/generate/dungeon` (Full Pipeline)

**Request:**
```json
{
  "guidelines": "Create a haunted castle with ghostly encounters",
  "options": {
    "room_count": 5,
    "layout_type": "line_graph",
    "include_contents": true,
    "include_atmosphere": true
  }
}
```

**Response:**
```json
{
  "dungeon": {
    "rooms": [
      {
        "id": "room_1",
        "name": "Grand Entrance Hall",
        "description": "A vast hall with crumbling stone walls...",
        "anchor": {"x": 0, "y": 0},
        "width": 8,
        "height": 6,
        "shape": "rectangle",
        "contents": ["stone pillars", "dusty tapestries"],
        "atmosphere": "Eerie silence broken by distant whispers",
        "challenges": ["hidden pressure plate"],
        "treasures": ["ancient coin"]
      }
    ],
    "connections": [
      {
        "room_a_id": "room_1",
        "room_b_id": "room_2",
        "connection_type": "door",
        "description": "Heavy oak door with iron hinges"
      }
    ],
    "metadata": {
      "generation_time": "2024-01-15T10:30:00Z",
      "model_used": "llama-4-scout-17b",
      "guidelines": "Create a haunted castle..."
    }
  },
  "status": "success"
}
```

## Class Hierarchy

```
BaseLayoutGenerator (abstract)
├── LineGraphLayoutGenerator
├── GridLayoutGenerator (future)
└── OrganicLayoutGenerator (future)

BaseContentGenerator (abstract)
├── LLMContentGenerator
└── TemplateContentGenerator (fallback)

DungeonGenerator (orchestrator)
├── layout_generator: BaseLayoutGenerator
├── content_generator: BaseContentGenerator
└── post_processor: PostProcessor
```

## File Structure

```
backend/
├── models/               # Data classes
│   ├── __init__.py
│   └── dungeon.py       # Dungeon-related models
└── src/dungeon/
    ├── __init__.py
    ├── generator.py     # Main orchestrator
    ├── utils.py         # Utility functions
    └── generators/
        ├── __init__.py
        ├── base.py      # Abstract base classes
        ├── layout.py    # Layout generation
        ├── content.py   # LLM content generation
        └── postprocess.py # Post-processing
```

## API Endpoints

### Full Pipeline
- `POST /api/generate/dungeon` - Complete dungeon generation

### Partial Workflows
- `POST /api/generate/guidelines` - Process user guidelines
- `POST /api/generate/layout` - Generate basic layout
- `POST /api/generate/dimensions` - Generate room dimensions
- `POST /api/generate/contents` - Generate room contents
- `POST /api/generate/postprocess` - Apply post-processing

### Utility Endpoints
- `GET /api/generate/models` - List available models
- `GET /api/generate/status` - Check generation status

## Implementation Priority

1. **Phase 1**: Core data classes and base layout generator
2. **Phase 2**: LLM integration for room dimensions
3. **Phase 3**: LLM integration for room contents
4. **Phase 4**: Post-processing and optimization
5. **Phase 5**: Additional layout types and features

## Error Handling

- **Validation**: Pydantic models for request/response validation
- **LLM Failures**: Graceful fallback to template-based generation
- **Partial Failures**: Return partial results with error indicators
- **Rate Limiting**: Handle API rate limits gracefully

## Configuration

- **Environment Variables**: API keys, model selection, generation parameters
- **Model Selection**: Configurable LLM models per generation step
- **Generation Parameters**: Room count, layout type, content detail level
