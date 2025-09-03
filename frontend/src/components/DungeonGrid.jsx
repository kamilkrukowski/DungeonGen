import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';

const GRID_SIZE = 50; // Size of each grid cell in pixels
const GRID_COLOR = '#e0e0e0'; // Faded grey color for grid lines
const ROOM_COLORS = [
  '#4CAF50', // Green
  '#2196F3', // Blue
  '#FF9800', // Orange
  '#9C27B0', // Purple
  '#F44336', // Red
  '#00BCD4', // Cyan
  '#FF5722', // Deep Orange
  '#795548', // Brown
];

const DungeonGrid = ({
  dungeonData = null,
  width = 800,
  height = 600,
  onRoomSelect = null,
  selectedRoomId = null
}) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [gridBounds, setGridBounds] = useState({ minX: -10, maxX: 10, minY: -10, maxY: 10 });
  const [actualWidth, setActualWidth] = useState(typeof width === 'number' ? width : 800);
  const [actualHeight, setActualHeight] = useState(height);
  const [hoveredRoom, setHoveredRoom] = useState(null);
  const [baseScale, setBaseScale] = useState(1); // The scale that represents "fit to viewport"

  // Helper method to get corridor styling based on hallway type
  const getCorridorStyle = useCallback((hallwayType) => {
    switch (hallwayType) {
      case 'narrow_passage':
        return { color: '#8B4513', borderColor: '#654321' }; // Brown
      case 'standard_door':
        return { color: '#696969', borderColor: '#404040' }; // Dark gray
      case 'wide_corridor':
        return { color: '#4682B4', borderColor: '#2F4F4F' }; // Steel blue
      case 'grand_hallway':
        return { color: '#DAA520', borderColor: '#B8860B' }; // Goldenrod
      case 'secret_tunnel':
        return { color: '#2F4F4F', borderColor: '#1C1C1C' }; // Dark slate
      default:
        console.warn('Unknown hallway type:', hallwayType, 'using default style');
        return { color: '#696969', borderColor: '#404040' }; // Default gray
    }
  }, []);

  // Calculate pan boundaries based on actual dungeon bounds and canvas size
  const getPanBoundaries = useCallback(() => {
    if (!dungeonData || !dungeonData.dungeon || !dungeonData.dungeon.rooms || dungeonData.dungeon.rooms.length === 0) {
      return { minX: -1000, maxX: 1000, minY: -1000, maxY: 1000 };
    }

    // Find the actual bounding box of all rooms
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    dungeonData.dungeon.rooms.forEach(room => {
      if (room.anchor) {
        minX = Math.min(minX, room.anchor.x);
        maxX = Math.max(maxX, room.anchor.x + room.width);
        minY = Math.min(minY, room.anchor.y);
        maxY = Math.max(maxY, room.anchor.y + room.height);
      }
    });

    if (minX === Infinity) {
      return { minX: -1000, maxX: 1000, minY: -1000, maxY: 1000 };
    }

    const actualScale = baseScale * scale;

    // Calculate dungeon bounds in screen coordinates
    const dungeonScreenMinX = minX * GRID_SIZE * actualScale;
    const dungeonScreenMaxX = maxX * GRID_SIZE * actualScale;
    const dungeonScreenMinY = minY * GRID_SIZE * actualScale;
    const dungeonScreenMaxY = maxY * GRID_SIZE * actualScale;

    // Calculate boundaries relative to the dungeon's centered position
    // The dungeon should be able to move with comfortable margins around its centered position
    const margin = Math.max(actualWidth, actualHeight) * 0.3; // 30% margin for comfortable panning

    // Calculate the dungeon's centered position (this is where position.x and position.y should be when centered)
    const centeredPositionX = actualWidth / 2 - ((minX + maxX) / 2) * GRID_SIZE * actualScale;
    const centeredPositionY = actualHeight / 2 - ((minY + maxY) / 2) * GRID_SIZE * actualScale;

    // Allow panning around the centered position with margins
    const minPanX = centeredPositionX - margin;  // Can pan left from center
    const maxPanX = centeredPositionX + margin;  // Can pan right from center
    const minPanY = centeredPositionY - margin;  // Can pan up from center
    const maxPanY = centeredPositionY + margin;  // Can pan down from center

    return {
      minX: minPanX,
      maxX: maxPanX,
      minY: minPanY,
      maxY: maxPanY
    };
  }, [dungeonData, baseScale, scale, actualWidth, actualHeight]);

  // Clamp position within boundaries
  const clampPosition = useCallback((pos) => {
    const boundaries = getPanBoundaries();
    return {
      x: Math.max(boundaries.minX, Math.min(boundaries.maxX, pos.x)),
      y: Math.max(boundaries.minY, Math.min(boundaries.maxY, pos.y))
    };
  }, [getPanBoundaries]);

  // Handle responsive width and container size changes
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const container = containerRef.current;
        const parentWidth = container.parentElement.clientWidth;

        if (typeof width === 'string' && width.includes('%')) {
          const percentage = parseInt(width) / 100;
          setActualWidth(parentWidth * percentage);
        } else if (typeof width === 'number') {
          setActualWidth(width);
        }

        // If we have dungeon data, refit it to the new viewport
        if (dungeonData && dungeonData.dungeon) {
          // Use a ref to avoid dependency issues
          setTimeout(() => {
            if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.rooms && dungeonData.dungeon.rooms.length > 0) {
              // Recalculate bounds and center
              let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

              dungeonData.dungeon.rooms.forEach(room => {
                if (room.anchor) {
                  minX = Math.min(minX, room.anchor.x);
                  maxX = Math.max(maxX, room.anchor.x + room.width);
                  minY = Math.min(minY, room.anchor.y);
                  maxY = Math.max(maxY, room.anchor.y + room.height);
                }
              });

              if (minX !== Infinity) {
                const dungeonWidth = maxX - minX;
                const dungeonHeight = maxY - minY;
                const padding = 0.15; // Increased padding for better view
                const scaleX = (actualWidth * (1 - padding)) / (dungeonWidth * GRID_SIZE);
                const scaleY = (actualHeight * (1 - padding)) / (dungeonHeight * GRID_SIZE);
                const newBaseScale = Math.min(scaleX, scaleY, 2);

                // Center the dungeon on the canvas
                const dungeonCenterX = (minX + maxX) / 2;
                const dungeonCenterY = (minY + maxY) / 2;

                // Calculate position so dungeon center appears at canvas center
                const newPosition = {
                  x: actualWidth / 2 - (dungeonCenterX * GRID_SIZE * newBaseScale),
                  y: actualHeight / 2 - (dungeonCenterY * GRID_SIZE * newBaseScale)
                };

                setBaseScale(newBaseScale);
                setScale(1);
                setPosition(newPosition);
              }
            }
          }, 50);
        }
      }
    };

    updateSize();

    // Use ResizeObserver for more reliable size detection
    let resizeObserver;
    if (containerRef.current) {
      resizeObserver = new ResizeObserver(updateSize);
      resizeObserver.observe(containerRef.current.parentElement);
    }

    // Also listen for window resize as fallback
    window.addEventListener('resize', updateSize);

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      window.removeEventListener('resize', updateSize);
    };
  }, [width, dungeonData, actualWidth, actualHeight]);

  // Calculate grid bounds based on dungeon viewport
  useEffect(() => {
    if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.viewport) {
      const viewport = dungeonData.dungeon.viewport;
      setGridBounds({
        minX: viewport.minX,
        maxX: viewport.maxX,
        minY: viewport.minY,
        maxY: viewport.maxY
      });
    } else if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.rooms.length > 0) {
      // Fallback: calculate bounds from rooms if no viewport
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

      dungeonData.dungeon.rooms.forEach(room => {
        if (room.anchor) {
          minX = Math.min(minX, room.anchor.x);
          maxX = Math.max(maxX, room.anchor.x + room.width);
          minY = Math.min(minY, room.anchor.y);
          maxY = Math.max(maxY, room.anchor.y + room.height);
        }
      });

      // Add padding
      const padding = 5;
      setGridBounds({
        minX: minX - padding,
        maxX: maxX + padding,
        minY: minY - padding,
        maxY: maxY + padding
      });
    }
  }, [dungeonData]);

  // Convert grid coordinates to screen coordinates
  const gridToScreen = useCallback((gridX, gridY) => {
    const actualScale = baseScale * scale;
    return {
      x: (gridX * GRID_SIZE * actualScale) + position.x,
      y: (gridY * GRID_SIZE * actualScale) + position.y
    };
  }, [baseScale, scale, position]);

  // Convert screen coordinates to grid coordinates
  const screenToGrid = useCallback((screenX, screenY) => {
    const actualScale = baseScale * scale;
    return {
      x: Math.round((screenX - position.x) / (GRID_SIZE * actualScale)),
      y: Math.round((screenY - position.y) / (GRID_SIZE * actualScale))
    };
  }, [baseScale, scale, position]);

  // Find room at screen coordinates
  const findRoomAtPosition = useCallback((screenX, screenY) => {
    if (!dungeonData || !dungeonData.dungeon) return null;

    const gridPos = screenToGrid(screenX, screenY);

    for (const room of dungeonData.dungeon.rooms) {
      if (room.anchor &&
          gridPos.x >= room.anchor.x &&
          gridPos.x < room.anchor.x + room.width &&
          gridPos.y >= room.anchor.y &&
          gridPos.y < room.anchor.y + room.height) {
        return room;
      }
    }
    return null;
  }, [dungeonData, screenToGrid]);

  // Draw the grid and rooms
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, actualWidth, actualHeight);

    // Set canvas size
    canvas.width = actualWidth;
    canvas.height = actualHeight;

    // Calculate actual scale for consistent scaling across all rendering
    const actualScale = baseScale * scale;

    // Draw grid lines
    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.3;

    const { minX, maxX, minY, maxY } = gridBounds;

    // Vertical lines
    for (let x = minX; x <= maxX; x++) {
      const start = gridToScreen(x, minY);
      const end = gridToScreen(x, maxY);
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    }

    // Horizontal lines
    for (let y = minY; y <= maxY; y++) {
      const start = gridToScreen(minX, y);
      const end = gridToScreen(maxX, y);
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    }

    // Draw corridors first (behind rooms)
    if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.corridors) {

      dungeonData.dungeon.corridors.forEach((corridor, index) => {

        // Defensive checks
        if (!corridor || !corridor.pathPoints || !Array.isArray(corridor.pathPoints)) {
          console.warn(`Invalid corridor data for corridor ${index}:`, corridor);
          return;
        }

        if (corridor.pathPoints.length < 2) {
          console.warn(`Corridor ${index} has insufficient path points:`, corridor.pathPoints);
          return;
        }

        // Validate path points
        for (let i = 0; i < corridor.pathPoints.length; i++) {
          const point = corridor.pathPoints[i];
          if (!point || typeof point.x !== 'number' || typeof point.y !== 'number') {
            console.warn(`Invalid path point ${i} in corridor ${index}:`, point);
            return;
          }
        }

        // Set corridor style based on hallway type
        const corridorStyle = getCorridorStyle(corridor.hallwayType);

        ctx.strokeStyle = corridorStyle.color;
        ctx.lineWidth = (corridor.width || 1) * 2 * actualScale; // Scale width with zoom, default to 1
        ctx.globalAlpha = 0.7;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        // Draw corridor path
        ctx.beginPath();
        const firstPoint = gridToScreen(corridor.pathPoints[0].x, corridor.pathPoints[0].y);
        ctx.moveTo(firstPoint.x, firstPoint.y);

        for (let i = 1; i < corridor.pathPoints.length; i++) {
          const point = gridToScreen(corridor.pathPoints[i].x, corridor.pathPoints[i].y);
          ctx.lineTo(point.x, point.y);
        }

        ctx.stroke();

        // Draw corridor border for better visibility
        ctx.strokeStyle = corridorStyle.borderColor;
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.9;
        ctx.stroke();
      });
    }

    // Draw rooms
    if (dungeonData && dungeonData.dungeon) {
      dungeonData.dungeon.rooms.forEach((room, index) => {
        if (!room.anchor) return;

        const screenPos = gridToScreen(room.anchor.x, room.anchor.y);
        const roomWidth = room.width * GRID_SIZE * actualScale;
        const roomHeight = room.height * GRID_SIZE * actualScale;
        const colorIndex = index % ROOM_COLORS.length;
        const isSelected = selectedRoomId === room.id;
        const isHovered = hoveredRoom && hoveredRoom.id === room.id;

        // Draw room rectangle
        ctx.fillStyle = ROOM_COLORS[colorIndex];
        ctx.globalAlpha = 0.8;
        ctx.fillRect(screenPos.x, screenPos.y, roomWidth, roomHeight);

        // Draw border
        ctx.strokeStyle = isSelected ? '#000' : '#333';
        ctx.lineWidth = isSelected ? 3 : 1;
        ctx.globalAlpha = 1;
        ctx.strokeRect(screenPos.x, screenPos.y, roomWidth, roomHeight);

        // Draw room name
        ctx.fillStyle = '#fff';
        ctx.font = `${12 * actualScale}px Arial`;
        ctx.fontWeight = 'bold';
        ctx.globalAlpha = 1;

        // Add shadow effect
        ctx.shadowColor = 'black';
        ctx.shadowBlur = 2;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 1;

        ctx.fillText(room.name || `Room ${room.id}`, screenPos.x + 5, screenPos.y + 15 * actualScale);

        // Reset shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
      });
    }
  }, [dungeonData, gridBounds, gridToScreen, selectedRoomId, hoveredRoom, scale, baseScale, actualWidth, actualHeight, getCorridorStyle]);

  // Redraw canvas when dependencies change
  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  // Handle mouse wheel for zooming
  const handleWheel = useCallback((e) => {
    e.preventDefault();

    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const oldScale = scale;
    const newScale = e.deltaY > 0 ? oldScale * 0.9 : oldScale * 1.1;
    const clampedScale = Math.max(0.8, Math.min(3, newScale));

    // Calculate new position to zoom towards mouse
    const scaleRatio = clampedScale / oldScale;
    const newX = mouseX - (mouseX - position.x) * scaleRatio;
    const newY = mouseY - (mouseY - position.y) * scaleRatio;

    setScale(clampedScale);
    setPosition({ x: newX, y: newY });
  }, [scale, position]);

  // Add wheel event listener with passive: false
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

          const wheelHandler = (e) => {
        e.preventDefault();

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const oldScale = scale;
        const newScale = e.deltaY > 0 ? oldScale * 0.9 : oldScale * 1.1;
        const clampedScale = Math.max(0.8, Math.min(3, newScale));

        // Calculate new position to zoom towards mouse
        // Convert mouse position to grid coordinates
        const actualScale = baseScale * oldScale;
        const mouseGridX = (mouseX - position.x) / (GRID_SIZE * actualScale);
        const mouseGridY = (mouseY - position.y) / (GRID_SIZE * actualScale);

                // Calculate new position to keep mouse at same grid position
        const newActualScale = baseScale * clampedScale;
        const newX = mouseX - (mouseGridX * GRID_SIZE * newActualScale);
        const newY = mouseY - (mouseGridY * GRID_SIZE * newActualScale);

        const clampedPosition = clampPosition({ x: newX, y: newY });

        setScale(clampedScale);
        setPosition(clampedPosition);
      };

    canvas.addEventListener('wheel', wheelHandler, { passive: false });

    return () => {
      canvas.removeEventListener('wheel', wheelHandler);
    };
  }, [scale, position, actualWidth, actualHeight, baseScale]);

  // Handle mouse down for panning
  const handleMouseDown = useCallback((e) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  }, [position]);

    // Handle mouse move for panning and hover
  const handleMouseMove = useCallback((e) => {
    if (isDragging) {
      const newPosition = {
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      };
      const clampedPosition = clampPosition(newPosition);
      setPosition(clampedPosition);
    } else {
      // Check for room hover
      const rect = canvasRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const room = findRoomAtPosition(mouseX, mouseY);
      setHoveredRoom(room);

      // Update cursor
      canvasRef.current.style.cursor = room ? 'pointer' : 'grab';
    }
  }, [isDragging, dragStart, findRoomAtPosition, clampPosition]);

  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Handle click for room selection
  const handleClick = useCallback((e) => {
    if (isDragging) return; // Don't select if we were dragging

    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const room = findRoomAtPosition(mouseX, mouseY);

    if (room && onRoomSelect) {
      onRoomSelect(room);
    }
  }, [isDragging, findRoomAtPosition, onRoomSelect]);

  // Zoom controls
  const handleZoomIn = () => {
    const oldScale = scale;
    const newScale = Math.min(3, oldScale * 1.2);

    // Zoom towards center of viewport (0,0 in grid coordinates)
    const actualScale = baseScale * oldScale;
    const centerGridX = -position.x / (GRID_SIZE * actualScale);
    const centerGridY = -position.y / (GRID_SIZE * actualScale);

    const newActualScale = baseScale * newScale;
    const newX = -(centerGridX * GRID_SIZE * newActualScale);
    const newY = -(centerGridY * GRID_SIZE * newActualScale);

    const clampedPosition = clampPosition({ x: newX, y: newY });

    setScale(newScale);
    setPosition(clampedPosition);
  };

  const handleZoomOut = () => {
    const oldScale = scale;
    const newScale = Math.max(0.8, oldScale / 1.2); // Min zoom is 0.8

    // Zoom towards center of viewport (0,0 in grid coordinates)
    const actualScale = baseScale * oldScale;
    const centerGridX = -position.x / (GRID_SIZE * actualScale);
    const centerGridY = -position.y / (GRID_SIZE * actualScale);

    const newActualScale = baseScale * newScale;
    const newX = -(centerGridX * GRID_SIZE * newActualScale);
    const newY = -(centerGridY * GRID_SIZE * newActualScale);

    const clampedPosition = clampPosition({ x: newX, y: newY });

    setScale(newScale);
    setPosition(clampedPosition);
  };

  const handleResetView = () => {
    if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.rooms && dungeonData.dungeon.rooms.length > 0) {
      // Recalculate bounds and center
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

      dungeonData.dungeon.rooms.forEach(room => {
        if (room.anchor) {
          minX = Math.min(minX, room.anchor.x);
          maxX = Math.max(maxX, room.anchor.x + room.width);
          minY = Math.min(minY, room.anchor.y);
          maxY = Math.max(maxY, room.anchor.y + room.height);
        }
      });

      if (minX !== Infinity) {
        const dungeonWidth = maxX - minX;
        const dungeonHeight = maxY - minY;
        const padding = 0.15; // Increased padding for better view
        const scaleX = (actualWidth * (1 - padding)) / (dungeonWidth * GRID_SIZE);
        const scaleY = (actualHeight * (1 - padding)) / (dungeonHeight * GRID_SIZE);
        const newBaseScale = Math.min(scaleX, scaleY, 2);

        // Center the dungeon on the canvas
        const dungeonCenterX = (minX + maxX) / 2;
        const dungeonCenterY = (minY + maxY) / 2;

        // Calculate position so dungeon center appears at canvas center
        const newPosition = {
          x: actualWidth / 2 - (dungeonCenterX * GRID_SIZE * newBaseScale),
          y: actualHeight / 2 - (dungeonCenterY * GRID_SIZE * newBaseScale)
        };

        setBaseScale(newBaseScale);
        setScale(1);
        setPosition(newPosition);
      }
    }
  };



  // Auto-fit when dungeon data changes (only once)
  useEffect(() => {
    if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.rooms && dungeonData.dungeon.rooms.length > 0) {
      // Small delay to ensure canvas is ready
      const timer = setTimeout(() => {
        // Recalculate bounds and center
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

        dungeonData.dungeon.rooms.forEach(room => {
          if (room.anchor) {
            minX = Math.min(minX, room.anchor.x);
            maxX = Math.max(maxX, room.anchor.x + room.width);
            minY = Math.min(minY, room.anchor.y);
            maxY = Math.max(maxY, room.anchor.y + room.height);
          }
        });

        if (minX !== Infinity) {
          const dungeonWidth = maxX - minX;
          const dungeonHeight = maxY - minY;
          const padding = 0.1;
          const scaleX = (actualWidth * (1 - padding)) / (dungeonWidth * GRID_SIZE);
          const scaleY = (actualHeight * (1 - padding)) / (dungeonHeight * GRID_SIZE);
          const newBaseScale = Math.min(scaleX, scaleY, 2);

          const dungeonCenterX = (minX + maxX) / 2;
          const dungeonCenterY = (minY + maxY) / 2;

          const newPosition = {
            x: actualWidth / 2 - (dungeonCenterX * GRID_SIZE * newBaseScale),
            y: actualHeight / 2 - (dungeonCenterY * GRID_SIZE * newBaseScale)
          };

          setBaseScale(newBaseScale);
          setScale(1);
          setPosition(newPosition);
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [dungeonData?.dungeon?.rooms, actualWidth, actualHeight]);

  return (
    <Box ref={containerRef} sx={{ position: 'relative', width: actualWidth, height }}>
      {/* Controls */}
      <Box sx={{
        position: 'absolute',
        top: 10,
        right: 10,
        zIndex: 100, // Lower z-index so settings panel can overlap
        display: 'flex',
        gap: 1,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderRadius: 1,
        padding: 1,
      }}>
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={handleZoomIn}>
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={handleZoomOut}>
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset View">
          <IconButton size="small" onClick={handleResetView}>
            <CenterFocusStrongIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Grid Info */}
      <Box sx={{
        position: 'absolute',
        top: 10,
        left: 10,
        zIndex: 100, // Lower z-index so settings panel can overlap
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderRadius: 1,
        padding: 1,
      }}>
        <Typography variant="caption" display="block">
          Scale: {scale.toFixed(2)}x
        </Typography>
        <Typography variant="caption" display="block">
          Grid: {GRID_SIZE}px
        </Typography>
        {dungeonData && dungeonData.dungeon && (
          <Typography variant="caption" display="block">
            Rooms: {dungeonData.dungeon.rooms.length}
          </Typography>
        )}
        {dungeonData && dungeonData.dungeon && dungeonData.dungeon.corridors && (
          <Typography variant="caption" display="block">
            Corridors: {dungeonData.dungeon.corridors.length}
          </Typography>
        )}
        {dungeonData && dungeonData.dungeon && dungeonData.dungeon.viewport && (
          <Typography variant="caption" display="block">
            Viewport: {dungeonData.dungeon.viewport.width}×{dungeonData.dungeon.viewport.height}
          </Typography>
        )}
        {hoveredRoom && (
          <Typography variant="caption" display="block">
                            Hover: {hoveredRoom.name || `Room ${hoveredRoom.id}`}
          </Typography>
        )}
      </Box>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={actualWidth}
        height={actualHeight}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleClick}
        style={{
          backgroundColor: '#fafafa',
          cursor: 'grab',
          display: 'block'
        }}
      />

      {/* Instructions */}
      {(!dungeonData || !dungeonData.dungeon || dungeonData.dungeon.rooms.length === 0) && (
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          color: 'text.secondary',
          pointerEvents: 'none',
        }}>
          <Typography variant="h6" gutterBottom>
            No Dungeon Data
          </Typography>
          <Typography variant="body2">
            Generate a dungeon to see it displayed here
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default DungeonGrid;
