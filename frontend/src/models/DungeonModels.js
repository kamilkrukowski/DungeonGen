/**
 * Frontend models for dungeon data structures
 * These mirror the backend models for type safety and data parsing
 */

export class Coordinates {
  constructor(x, y) {
    this.x = x;
    this.y = y;
  }

  static fromObject(obj) {
    return new Coordinates(obj.x, obj.y);
  }

  add(other) {
    return new Coordinates(this.x + other.x, this.y + other.y);
  }

  sub(other) {
    return new Coordinates(this.x - other.x, this.y - other.y);
  }
}

export class CanvasViewport {
  constructor(minX, minY, maxX, maxY, margin = 5) {
    this.minX = minX;
    this.minY = minY;
    this.maxX = maxX;
    this.maxY = maxY;
    this.margin = margin;
  }

  static fromObject(obj) {
    if (!obj) return null;
    return new CanvasViewport(obj.min_x, obj.min_y, obj.max_x, obj.max_y, obj.margin);
  }

  get width() {
    return this.maxX - this.minX;
  }

  get height() {
    return this.maxY - this.minY;
  }

  get center() {
    return new Coordinates(
      Math.floor((this.minX + this.maxX) / 2),
      Math.floor((this.minY + this.maxY) / 2)
    );
  }

  static fromRooms(rooms, margin = 5) {
    if (!rooms || rooms.length === 0) {
      return new CanvasViewport(-10, -10, 10, 10, margin);
    }

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    rooms.forEach(room => {
      if (room.anchor) {
        minX = Math.min(minX, room.anchor.x);
        maxX = Math.max(maxX, room.anchor.x + room.width);
        minY = Math.min(minY, room.anchor.y);
        maxY = Math.max(maxY, room.anchor.y + room.height);
      }
    });

    return new CanvasViewport(
      minX - margin,
      minY - margin,
      maxX + margin,
      maxY + margin,
      margin
    );
  }
}

export class Room {
  constructor(id, name, description, anchor, width, height, shape, hasTraps = false, hasTreasure = false, hasMonsters = false) {
    this.id = id;
    this.name = name;
    this.description = description;
    this.anchor = anchor;
    this.width = width;
    this.height = height;
    this.shape = shape;
    this.hasTraps = hasTraps;
    this.hasTreasure = hasTreasure;
    this.hasMonsters = hasMonsters;
  }

  static fromObject(obj) {
    return new Room(
      obj.id,
      obj.name,
      obj.description,
      obj.anchor ? Coordinates.fromObject(obj.anchor) : null,
      obj.width,
      obj.height,
      obj.shape,
      obj.has_traps || false,
      obj.has_treasure || false,
      obj.has_monsters || false
    );
  }

  get bounds() {
    if (!this.anchor) {
      throw new Error("Room anchor not set");
    }
    return [
      this.anchor,
      new Coordinates(this.anchor.x + this.width, this.anchor.y + this.height)
    ];
  }

  get center() {
    if (!this.anchor) {
      throw new Error("Room anchor not set");
    }
    return new Coordinates(
      this.anchor.x + Math.floor(this.width / 2),
      this.anchor.y + Math.floor(this.height / 2)
    );
  }
}

export class Connection {
  constructor(roomAId, roomBId, connectionType = 'door', description = null) {
    this.roomAId = roomAId;
    this.roomBId = roomBId;
    this.connectionType = connectionType;
    this.description = description;
  }

  static fromObject(obj) {
    return new Connection(
      obj.room_a_id,
      obj.room_b_id,
      obj.connection_type,
      obj.description
    );
  }
}

export class RoomContent {
  constructor(roomId, name, description, contents = [], atmosphere = '', challenges = [], treasures = [], hasTraps = false, hasTreasure = false, hasMonsters = false) {
    this.roomId = roomId;
    this.name = name;
    this.description = description;
    this.contents = contents;
    this.atmosphere = atmosphere;
    this.challenges = challenges;
    this.treasures = treasures;
    this.hasTraps = hasTraps;
    this.hasTreasure = hasTreasure;
    this.hasMonsters = hasMonsters;
  }

  static fromObject(obj) {
    return new RoomContent(
      obj.room_id,
      obj.name,
      obj.description,
      obj.contents || [],
      obj.atmosphere || '',
      obj.challenges || [],
      obj.treasures || [],
      obj.has_traps || false,
      obj.has_treasure || false,
      obj.has_monsters || false
    );
  }
}

export class DungeonLayout {
  constructor(rooms = [], connections = [], corridors = [], metadata = {}, viewport = null) {
    this.rooms = rooms;
    this.connections = connections;
    this.corridors = corridors;  // NEW: corridor paths
    this.metadata = metadata;
    this.viewport = viewport;
  }

  static fromObject(obj) {
    const rooms = (obj.rooms || []).map(room => Room.fromObject(room));
    const connections = (obj.connections || []).map(conn => Connection.fromObject(conn));
    const corridors = (obj.corridors || []).map(corridor => CorridorPath.fromObject(corridor));  // NEW: parse corridors
    const viewport = CanvasViewport.fromObject(obj.viewport) || CanvasViewport.fromRooms(rooms);

    // Parse room contents from metadata if available
    const roomContents = {};
    if (obj.metadata && obj.metadata.room_contents) {
      Object.entries(obj.metadata.room_contents).forEach(([roomId, contentData]) => {
        roomContents[roomId] = RoomContent.fromObject(contentData);
      });
    }

    const metadata = { ...obj.metadata, roomContents };
    return new DungeonLayout(rooms, connections, corridors, metadata, viewport);  // NEW: include corridors
  }

  getRoomContent(roomId) {
    return this.metadata.roomContents?.[roomId] || null;
  }
}

export class CorridorPath {
  constructor(connectionId, roomAId, roomBId, pathPoints, width, hallwayType, description = null) {
    this.connectionId = connectionId;
    this.roomAId = roomAId;
    this.roomBId = roomBId;
    this.pathPoints = pathPoints;
    this.width = width;
    this.hallwayType = hallwayType;
    this.description = description;
  }

  static fromObject(obj) {
    console.log('Parsing corridor object:', obj);

    if (!obj.path_points || !Array.isArray(obj.path_points)) {
      console.error('Invalid path_points in corridor:', obj);
      throw new Error('Invalid path_points in corridor data');
    }

    const pathPoints = obj.path_points.map(p => {
      console.log('Parsing path point:', p);
      return Coordinates.fromObject(p);
    });

    console.log('Parsed path points:', pathPoints);

    return new CorridorPath(
      obj.connection_id,
      obj.room_a_id,
      obj.room_b_id,
      pathPoints,
      obj.width,
      obj.hallway_type,
      obj.description
    );
  }
}

export class DungeonGuidelines {
  constructor(theme, atmosphere, difficulty = 'medium', roomCount = 5, layoutType = 'line_graph', specialRequirements = [], percentageRoomsTrapped = 0.15, percentageRoomsWithTreasure = 0.20, percentageRoomsWithMonsters = 0.45) {
    this.theme = theme;
    this.atmosphere = atmosphere;
    this.difficulty = difficulty;
    this.roomCount = roomCount;
    this.layoutType = layoutType;
    this.specialRequirements = specialRequirements;
    this.percentageRoomsTrapped = percentageRoomsTrapped;
    this.percentageRoomsWithTreasure = percentageRoomsWithTreasure;
    this.percentageRoomsWithMonsters = percentageRoomsWithMonsters;
  }

  static fromObject(obj) {
    return new DungeonGuidelines(
      obj.theme,
      obj.atmosphere,
      obj.difficulty,
      obj.room_count,
      obj.layout_type,
      obj.special_requirements || [],
      obj.percentage_rooms_trapped || 0.15,
      obj.percentage_rooms_with_treasure || 0.20,
      obj.percentage_rooms_with_monsters || 0.45
    );
  }
}

export class GenerationOptions {
  constructor(includeContents = true, includeAtmosphere = true, includeChallenges = true, includeTreasures = true, llmModel = 'meta-llama/llama-4-scout-17b-16e-instruct') {
    this.includeContents = includeContents;
    this.includeAtmosphere = includeAtmosphere;
    this.includeChallenges = includeChallenges;
    this.includeTreasures = includeTreasures;
    this.llmModel = llmModel;
  }

  static fromObject(obj) {
    return new GenerationOptions(
      obj.include_contents,
      obj.include_atmosphere,
      obj.include_challenges,
      obj.include_treasures,
      obj.llm_model
    );
  }
}

export class DungeonResult {
  constructor(dungeon, guidelines, options, generationTime, status = 'success', errors = []) {
    this.dungeon = dungeon;
    this.guidelines = guidelines;
    this.options = options;
    this.generationTime = generationTime;
    this.status = status;
    this.errors = errors;
  }

  static fromObject(obj) {
    return new DungeonResult(
      DungeonLayout.fromObject(obj.dungeon),
      DungeonGuidelines.fromObject(obj.guidelines),
      GenerationOptions.fromObject(obj.options),
      obj.generation_time,
      obj.status,
      obj.errors || []
    );
  }
}

/**
 * Parse dungeon data from the backend response
 * @param {Object} responseData - The raw response from the backend
 * @returns {DungeonResult} - Parsed dungeon result
 */
export function parseDungeonData(responseData) {
  try {
    return DungeonResult.fromObject(responseData);
  } catch (error) {
    console.error('Error parsing dungeon data:', error);
    throw new Error('Failed to parse dungeon data from backend response');
  }
}
