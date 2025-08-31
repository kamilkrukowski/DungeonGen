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

  // Calculate pan boundaries based on dungeon viewport
  const getPanBoundaries = useCallback(() => {
    if (!dungeonData || !dungeonData.dungeon || !dungeonData.dungeon.viewport) {
      return { minX: -1000, maxX: 1000, minY: -1000, maxY: 1000 };
    }

    const viewport = dungeonData.dungeon.viewport;
    const actualScale = baseScale * scale;

    // Calculate dungeon size in screen coordinates
    const dungeonWidth = viewport.width * GRID_SIZE * actualScale;
    const dungeonHeight = viewport.height * GRID_SIZE * actualScale;

    // Use the larger dimension divided by 2 for both axes
    const largerDimension = Math.max(dungeonWidth, dungeonHeight);
    const margin = largerDimension / 2.0;

    const minX = -margin;
    const maxX = margin;
    const minY = -margin;
    const maxY = margin;

    return { minX, maxX, minY, maxY };
  }, [dungeonData, baseScale, scale]);

  // Clamp position within boundaries
  const clampPosition = useCallback((pos) => {
    const boundaries = getPanBoundaries();
    return {
      x: Math.max(boundaries.minX, Math.min(boundaries.maxX, pos.x)),
      y: Math.max(boundaries.minY, Math.min(boundaries.maxY, pos.y))
    };
  }, [getPanBoundaries]);

  // Handle responsive width
  useEffect(() => {
    if (typeof width === 'string' && width.includes('%')) {
      const updateSize = () => {
        if (containerRef.current) {
          const container = containerRef.current;
          const parentWidth = container.parentElement.clientWidth;
          const percentage = parseInt(width) / 100;
          setActualWidth(parentWidth * percentage);
        }
      };

      updateSize();
      window.addEventListener('resize', updateSize);
      return () => window.removeEventListener('resize', updateSize);
    } else if (typeof width === 'number') {
      setActualWidth(width);
    }
  }, [width]);

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

    // Draw rooms
    if (dungeonData && dungeonData.dungeon) {
      dungeonData.dungeon.rooms.forEach((room, index) => {
        if (!room.anchor) return;

        const screenPos = gridToScreen(room.anchor.x, room.anchor.y);
        const actualScale = baseScale * scale;
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

        ctx.fillText(room.name, screenPos.x + 5, screenPos.y + 15 * actualScale);

        // Reset shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
      });
    }
  }, [dungeonData, gridBounds, gridToScreen, selectedRoomId, hoveredRoom, scale, baseScale, actualWidth, actualHeight]);

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
    fitDungeonToViewport();
  };

  // Auto-fit dungeon to viewport
  const fitDungeonToViewport = useCallback(() => {
    if (!dungeonData || !dungeonData.dungeon || !dungeonData.dungeon.viewport) return;

    const viewport = dungeonData.dungeon.viewport;
    const viewportWidth = viewport.width;
    const viewportHeight = viewport.height;

    // Calculate scale to fit the viewport in the canvas
    const scaleX = (actualWidth * 0.8) / (viewportWidth * GRID_SIZE);
    const scaleY = (actualHeight * 0.8) / (viewportHeight * GRID_SIZE);
    const newBaseScale = Math.min(scaleX, scaleY, 2); // Cap at 2x zoom

    // Center the dungeon on the canvas by offsetting the position
    // This makes clamping much simpler since the dungeon is at (0,0) relative to canvas center
    const newPosition = {
      x: actualWidth / 2 - (viewportWidth * GRID_SIZE * newBaseScale) / 2,
      y: actualHeight / 2 - (viewportHeight * GRID_SIZE * newBaseScale) / 2
    };

    setBaseScale(newBaseScale);
    setScale(1); // Reset to 1.0 (which now represents the fit-to-viewport scale)
    setPosition(newPosition);
  }, [dungeonData, actualWidth, actualHeight]);

  // Auto-fit when dungeon data changes (only once)
  useEffect(() => {
    if (dungeonData && dungeonData.dungeon && dungeonData.dungeon.viewport) {
      // Small delay to ensure canvas is ready
      const timer = setTimeout(fitDungeonToViewport, 100);
      return () => clearTimeout(timer);
    }
  }, [dungeonData?.dungeon?.viewport]); // Only depend on viewport changes, not the function

  return (
    <Box ref={containerRef} sx={{ position: 'relative', width: actualWidth, height }}>
      {/* Controls */}
      <Box sx={{
        position: 'absolute',
        top: 10,
        right: 10,
        zIndex: 1000,
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
        zIndex: 1000,
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
        {dungeonData && dungeonData.dungeon && dungeonData.dungeon.viewport && (
          <Typography variant="caption" display="block">
            Viewport: {dungeonData.dungeon.viewport.width}×{dungeonData.dungeon.viewport.height}
          </Typography>
        )}
        {hoveredRoom && (
          <Typography variant="caption" display="block">
            Hover: {hoveredRoom.name}
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
