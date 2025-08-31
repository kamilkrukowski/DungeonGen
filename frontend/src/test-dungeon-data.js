/**
 * Test data for dungeon parsing functionality
 * This simulates the backend response structure
 */

export const sampleDungeonResponse = {
  "dungeon": {
    "rooms": [
      {
        "id": "room_1",
        "name": "Entrance Hall",
        "description": "A grand entrance hall with stone pillars",
        "anchor": {"x": 0, "y": 0},
        "width": 3,
        "height": 2,
        "shape": "rectangle"
      },
      {
        "id": "room_2",
        "name": "Treasure Room",
        "description": "A hidden chamber filled with gold and jewels",
        "anchor": {"x": 4, "y": 1},
        "width": 2,
        "height": 2,
        "shape": "rectangle"
      },
      {
        "id": "room_3",
        "name": "Guard Chamber",
        "description": "A room where guards once stood watch",
        "anchor": {"x": 2, "y": 3},
        "width": 2,
        "height": 1,
        "shape": "rectangle"
      }
    ],
    "connections": [
      {
        "room_a_id": "room_1",
        "room_b_id": "room_2",
        "connection_type": "door",
        "description": "A heavy wooden door"
      },
      {
        "room_a_id": "room_1",
        "room_b_id": "room_3",
        "connection_type": "passage",
        "description": "A narrow stone passage"
      }
    ],
    "metadata": {
      "theme": "medieval castle",
      "difficulty": "medium"
    },
    "viewport": {
      "min_x": -1,
      "min_y": -1,
      "max_x": 6,
      "max_y": 4,
      "margin": 5
    }
  },
  "guidelines": {
    "theme": "medieval castle",
    "atmosphere": "dark and mysterious",
    "difficulty": "medium",
    "room_count": 3,
    "layout_type": "line_graph",
    "special_requirements": ["treasure room", "guard post"]
  },
  "options": {
    "include_contents": true,
    "include_atmosphere": true,
    "include_challenges": true,
    "include_treasures": true,
    "llm_model": "meta-llama/llama-4-scout-17b-16e-instruct"
  },
  "generation_time": "2024-01-15T10:30:00",
  "status": "success",
  "errors": []
};

// Test the parsing function
import { parseDungeonData } from './models/DungeonModels';

export function testDungeonParsing() {
  try {
    const parsed = parseDungeonData(sampleDungeonResponse);
    console.log('✅ Dungeon parsing successful!');
    console.log('Parsed dungeon:', parsed);
    console.log('Room count:', parsed.dungeon.rooms.length);
    console.log('First room:', parsed.dungeon.rooms[0]);
    return true;
  } catch (error) {
    console.error('❌ Dungeon parsing failed:', error);
    return false;
  }
}
