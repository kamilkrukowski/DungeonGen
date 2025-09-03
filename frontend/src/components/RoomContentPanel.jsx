import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  Paper,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import WarningIcon from '@mui/icons-material/Warning';
import DiamondIcon from '@mui/icons-material/Diamond';
import PetsIcon from '@mui/icons-material/Pets';
import InfoIcon from '@mui/icons-material/Info';

const RoomContentPanel = ({ parsedDungeonData, selectedRoomId }) => {
  if (!parsedDungeonData || !selectedRoomId) {
    return (
      <Box p={2}>
        <Typography variant="h6" color="text.secondary">
          Select a room to view its content
        </Typography>
      </Box>
    );
  }

  const selectedRoom = parsedDungeonData.dungeon.rooms.find(room => room.id === selectedRoomId);
  const roomContent = parsedDungeonData.dungeon.getRoomContent(selectedRoomId);

  if (!selectedRoom) {
    return (
      <Box p={2}>
        <Typography variant="h6" color="error">
          Room not found
        </Typography>
      </Box>
    );
  }

  if (!roomContent) {
    return (
      <Box p={2}>
        <Typography variant="h6" color="text.secondary">
          No content available for this room
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Debug: Room ID {selectedRoomId} not found in metadata.roomContents
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Available room IDs: {Object.keys(parsedDungeonData.dungeon.metadata.roomContents || {}).join(', ')}
        </Typography>
      </Box>
    );
  }

  const renderTrapContent = (trap, index) => (
    <Card key={index} variant="outlined" sx={{ mb: 1 }}>
      <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
        <Typography variant="subtitle2" color="error" gutterBottom>
          {trap.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Trigger:</strong> {trap.trigger}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Effect:</strong> {trap.effect}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Difficulty:</strong> {trap.difficulty}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Location:</strong> {trap.location}
        </Typography>
      </CardContent>
    </Card>
  );

  const renderTreasureContent = (treasure, index) => (
    <Card key={index} variant="outlined" sx={{ mb: 1 }}>
      <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
        <Typography variant="subtitle2" color="primary" gutterBottom>
          {treasure.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          {treasure.description}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Value:</strong> {treasure.value}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Location:</strong> {treasure.location}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Requirements:</strong> {treasure.requirements}
        </Typography>
      </CardContent>
    </Card>
  );

  const renderMonsterContent = (monster, index) => (
    <Card key={index} variant="outlined" sx={{ mb: 1 }}>
      <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
        <Typography variant="subtitle2" color="warning.main" gutterBottom>
          {monster.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          {monster.description}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Stats:</strong> {monster.stats}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Behavior:</strong> {monster.behavior}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Location:</strong> {monster.location}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box p={2} sx={{ maxHeight: '100vh', overflow: 'auto' }}>
      {/* Room Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
        <Typography variant="h5" gutterBottom>
          {roomContent.name}
        </Typography>
        <Chip
          label={roomContent.purpose}
          size="small"
          sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'inherit' }}
        />

        {/* Content Flags Display */}
        {selectedRoom && (
          <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {/* Special Room Flags */}
            {selectedRoom.isBossRoom && (
              <Chip
                label="Boss Room"
                size="small"
                sx={{
                  bgcolor: 'error.main',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
            )}
            {selectedRoom.isEntrance && (
              <Chip
                label="Entrance"
                size="small"
                sx={{
                  bgcolor: 'success.main',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
            )}

            {selectedRoom.isTreasureVault && (
              <Chip
                label="Treasure Vault"
                size="small"
                sx={{
                  bgcolor: 'warning.main',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
            )}

            {/* Content Type Flags */}
            {selectedRoom.hasTraps && (
              <Chip
                icon={<WarningIcon />}
                label="Traps"
                size="small"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'inherit',
                  border: '1px solid rgba(255,255,255,0.3)'
                }}
              />
            )}
            {selectedRoom.hasTreasure && (
              <Chip
                icon={<DiamondIcon />}
                label="Treasure"
                size="small"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'inherit',
                  border: '1px solid rgba(255,255,255,0.3)'
                }}
              />
            )}
            {selectedRoom.hasMonsters && (
              <Chip
                icon={<PetsIcon />}
                label="Monsters"
                size="small"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'inherit',
                  border: '1px solid rgba(255,255,255,0.3)'
                }}
              />
            )}
          </Box>
        )}

        {selectedRoom && (
          <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
            Room {selectedRoom.id} • {selectedRoom.width}×{selectedRoom.height} units
          </Typography>
        )}
      </Paper>

      {/* Player Description */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<InfoIcon />}>
          <Typography variant="h6">Player Description</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body1" paragraph>
            {roomContent.playerDescription}
          </Typography>
        </AccordionDetails>
      </Accordion>

      {/* GM Description */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Game Master Details</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body1" paragraph>
            {roomContent.gmDescription}
          </Typography>
        </AccordionDetails>
      </Accordion>

      {/* Traps */}
      {roomContent.traps && roomContent.traps.length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <WarningIcon color="error" />
              <Typography variant="h6">Traps ({roomContent.traps.length})</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {roomContent.traps.map(renderTrapContent)}
          </AccordionDetails>
        </Accordion>
      )}

      {/* Treasures */}
      {roomContent.treasures && roomContent.treasures.length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <DiamondIcon color="primary" />
              <Typography variant="h6">Treasures ({roomContent.treasures.length})</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {roomContent.treasures.map(renderTreasureContent)}
          </AccordionDetails>
        </Accordion>
      )}

      {/* Monsters */}
      {roomContent.monsters && roomContent.monsters.length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <PetsIcon color="warning" />
              <Typography variant="h6">Monsters ({roomContent.monsters.length})</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {roomContent.monsters.map(renderMonsterContent)}
          </AccordionDetails>
        </Accordion>
      )}

      {/* No Content Message */}
      {(!roomContent.traps || roomContent.traps.length === 0) &&
       (!roomContent.treasures || roomContent.treasures.length === 0) &&
       (!roomContent.monsters || roomContent.monsters.length === 0) && (
        <Paper elevation={1} sx={{ p: 2, mt: 2, bgcolor: 'grey.100' }}>
          <Typography variant="body2" color="text.secondary" align="center">
            This room contains no special content (traps, treasures, or monsters).
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default RoomContentPanel;
