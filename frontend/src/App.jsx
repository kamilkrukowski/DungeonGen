import { useState } from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Button from '@mui/material/Button'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Castle from '@mui/icons-material/Castle'
import GridViewIcon from '@mui/icons-material/GridView'
import SettingsIcon from '@mui/icons-material/Settings'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import Slider from '@mui/material/Slider'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Tooltip from '@mui/material/Tooltip'
import IconButton from '@mui/material/IconButton'
import './App.css'
import DungeonGrid from './components/DungeonGrid'
import { parseDungeonData } from './models/DungeonModels'

// Create a custom theme with dungeon-inspired colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#2c3e50',
      dark: '#1a252f',
    },
    secondary: {
      main: '#8e44ad',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#7f8c8d',
    },
  },
  typography: {
    h1: {
      fontWeight: 700,
      fontSize: '3.5rem',
      '@media (max-width:600px)': {
        fontSize: '2.5rem',
      },
    },
    h2: {
      fontWeight: 600,
      fontSize: '2.5rem',
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.8rem',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          padding: '12px 24px',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
          },
        },
      },
    },
  },
});

// Dungeon Content Component (Main Content)
function DungeonContent({
  message,
  setMessage,
  loading,
  error,
  dungeonResult,
  parsedDungeonData,
  selectedRoomId,
  showGrid,
  setShowGrid,
  onRoomSelect,
  onSubmit,
  onClear
}) {
  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      {/* Content */}
      <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1 }}>
        <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
          Describe the type of dungeon you want to generate. Be specific about themes, challenges, or special features!
        </Typography>

        {/* Dungeon Grid Display */}
        {showGrid && parsedDungeonData && (
          <Card sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                Dungeon Layout Visualization
              </Typography>
              <Box sx={{
                width: '100%',
                height: 600,
                border: '1px solid #e0e0e0',
                borderRadius: 1,
                overflow: 'hidden'
              }}>
                <DungeonGrid
                  dungeonData={parsedDungeonData}
                  width="100%"
                  height={600}
                  onRoomSelect={onRoomSelect}
                  selectedRoomId={selectedRoomId}
                />
              </Box>
                              {selectedRoomId && (
                  <Box sx={{ mt: 2, p: 2, backgroundColor: 'white', borderRadius: 1 }}>
                    {parsedDungeonData && parsedDungeonData.dungeon && (() => {
                      try {
                        const selectedRoom = parsedDungeonData.dungeon.rooms.find(room => room.id === selectedRoomId);
                        const roomContent = parsedDungeonData.dungeon.getRoomContent(selectedRoomId);

                        return (
                          <Box>
                            <Typography variant="h6" sx={{ mb: 1, color: 'primary.main' }}>
                              Room: {selectedRoom?.name || `Room ${selectedRoomId}`}
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              <strong>Description:</strong> {selectedRoom?.description || 'No description available'}
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              <strong>Size:</strong> {selectedRoom?.width && selectedRoom?.height ? `${selectedRoom.width} × ${selectedRoom.height}` : 'Unknown'}
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              <strong>Shape:</strong> {selectedRoom?.shape || 'Rectangle'}
                            </Typography>
                            {roomContent && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="body2" sx={{ mb: 0.5 }}>
                                  <strong>Atmosphere:</strong> {roomContent.atmosphere || 'None specified'}
                                </Typography>
                                {roomContent.contents && roomContent.contents.length > 0 && (
                                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                                    <strong>Contents:</strong> {roomContent.contents.join(', ')}
                                  </Typography>
                                )}
                                {roomContent.challenges && roomContent.challenges.length > 0 && (
                                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                                    <strong>Challenges:</strong> {roomContent.challenges.join(', ')}
                                  </Typography>
                                )}
                                {roomContent.treasures && roomContent.treasures.length > 0 && (
                                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                                    <strong>Treasures:</strong> {roomContent.treasures.join(', ')}
                                  </Typography>
                                )}
                              </Box>
                            )}
                          </Box>
                        );
                      } catch (error) {
                        console.error('Error displaying room details:', error);
                        return (
                          <Typography variant="body2" color="error">
                            Error loading room details. Please try selecting the room again.
                          </Typography>
                        );
                      }
                    })()}
                  </Box>
                )}
            </CardContent>
          </Card>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Dungeon Result Display (JSON) - Only show if grid is hidden */}
        {dungeonResult && !showGrid && (
          <Card sx={{ mb: 2, backgroundColor: '#f8f9fa' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                Generated Dungeon Structure (JSON)
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={8}
                variant="outlined"
                value={JSON.stringify(dungeonResult, null, 2)}
                InputProps={{
                  readOnly: true,
                  style: { fontFamily: 'monospace', fontSize: '0.875rem' }
                }}
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary">
                Status: {dungeonResult.status} |
                Generated at: {new Date(dungeonResult.generation_time).toLocaleString()}
                {dungeonResult.errors.length > 0 && ` | Errors: ${dungeonResult.errors.join(', ')}`}
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* Message Input */}
        <form onSubmit={onSubmit}>
          <TextField
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            placeholder="e.g., Create a haunted castle dungeon with ghostly encounters, hidden passages, and a cursed treasure room..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={loading}
            sx={{ mb: 2 }}
          />

          {/* Generate Button */}
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !message.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <Castle />}
            fullWidth
          >
            {loading ? 'Generating...' : 'Generate Dungeon'}
          </Button>
        </form>
      </Box>
    </Box>
  );
}

// Dungeon Sidebar Component
function DungeonSidebar({
  settings,
  onSettingsChange,
  expanded,
  onToggle
}) {
  return (
    <Box sx={{
      width: expanded ? 300 : 50,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.3s ease-in-out',
      backgroundColor: 'transparent'
    }}>
      {/* Settings Content */}
      {expanded && (
        <Box sx={{
          p: 3,
          flexGrow: 1,
          backgroundColor: 'white',
          borderLeft: '1px solid #e0e0e0',
          borderTop: '1px solid #e0e0e0'
        }}>
          <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
            Generation Parameters
          </Typography>

          {/* Number of Rooms */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
              Number of Rooms: {settings.roomCount}
            </Typography>
            <Slider
              value={settings.roomCount}
              onChange={(_, value) => onSettingsChange('roomCount', value)}
              min={3}
              max={20}
              step={1}
              marks={[
                { value: 3, label: '3' },
                { value: 10, label: '10' },
                { value: 20, label: '20' }
              ]}
              valueLabelDisplay="auto"
              sx={{ mt: 1 }}
            />
          </Box>

          {/* Layout Type */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
              Layout Type
            </Typography>
            <Tooltip title="Poisson Disc layout creates natural-looking room distributions with optimal spacing" placement="top">
              <FormControl fullWidth size="small">
                <Select
                  value={settings.layoutType}
                  onChange={(e) => onSettingsChange('layoutType', e.target.value)}
                  displayEmpty
                  disabled
                  sx={{
                    backgroundColor: '#f8f9fa',
                    '& .MuiSelect-select': { color: '#666' }
                  }}
                >
                  <MenuItem value="poisson_disc">Poisson Disc</MenuItem>
                </Select>
              </FormControl>
            </Tooltip>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
              Hover for description
            </Typography>
          </Box>

          {/* Current Settings Display */}
          <Card sx={{ backgroundColor: '#f8f9fa', p: 2, border: '1px solid #e0e0e0' }}>
            <Typography variant="body2" sx={{ mb: 1, fontWeight: 600, color: 'primary.main' }}>
              Current Settings
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              Rooms: {settings.roomCount}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              Layout: Poisson Disc
            </Typography>
          </Card>
        </Box>
      )}
    </Box>
  );
}

// Main Dungeon Generator Component
function DungeonGenerator() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dungeonResult, setDungeonResult] = useState(null);
  const [parsedDungeonData, setParsedDungeonData] = useState(null);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [showGrid, setShowGrid] = useState(true); // Enable grid by default
  const [settingsExpanded, setSettingsExpanded] = useState(true); // Expanded by default
  const [settings, setSettings] = useState({
    roomCount: 10,
    layoutType: 'poisson_disc'
  });

  const handleDungeonGenerate = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setError('');
    setDungeonResult(null);
    setParsedDungeonData(null);
    setShowGrid(true); // Always show grid after generation
    setSelectedRoomId(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/generate/dungeon`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          guidelines: message,
          options: {
            room_count: settings.roomCount,
            layout_type: settings.layoutType
          }
        }),
      });

      const data = await response.json();
      console.log('Received dungeon data:', data);

      if (data.status === 'success') {
        setDungeonResult(data);

        try {
          const parsed = parseDungeonData(data);
          console.log('Successfully parsed dungeon data:', parsed);
          setParsedDungeonData(parsed);
        } catch (parseError) {
          console.error('Error parsing dungeon data:', parseError);
          console.error('Raw data that failed to parse:', data);
          setError('Generated dungeon data could not be parsed for display');
        }
      } else {
        setError(data.error || 'Failed to generate structured dungeon');
      }
    } catch (err) {
      setError('Network error. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setError('');
    setDungeonResult(null);
    setParsedDungeonData(null);
    setShowGrid(true); // Keep grid visible
    setSelectedRoomId(null);
    setMessage('');
  };

  const handleRoomSelect = (room) => {
    setSelectedRoomId(room.id);
  };

  const handleSettingsChange = (setting, value) => {
    setSettings(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  const toggleSettings = () => {
    setSettingsExpanded(!settingsExpanded);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleDungeonGenerate();
  };

  return (
    <Paper sx={{
      minHeight: '800px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      borderRadius: 3,
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Shared Header Cap */}
      <Box sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        p: 2,
        minHeight: 64,
        width: '100%',
        position: 'relative',
        zIndex: 2
      }}>
        <Typography variant="h6">
          <Castle sx={{ mr: 1, verticalAlign: 'middle' }} />
          Dungeon Generator
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {parsedDungeonData && (
            <Button
              onClick={() => setShowGrid(!showGrid)}
              sx={{ color: 'white', fontSize: '0.8rem' }}
              size="small"
              startIcon={<GridViewIcon />}
            >
              {showGrid ? 'Hide Grid' : 'Show Grid'}
            </Button>
          )}
          <Button
            onClick={clearHistory}
            sx={{ color: 'white', fontSize: '0.8rem' }}
            size="small"
          >
            Clear
          </Button>
          <IconButton
            onClick={toggleSettings}
            sx={{ color: 'white' }}
            size="small"
          >
            <SettingsIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Content Area */}
      <Box sx={{
        flex: 1,
        display: 'flex',
        position: 'relative'
      }}>
        {/* Main Content */}
        <Box sx={{
          flex: 1,
          marginRight: settingsExpanded ? '300px' : '50px',
          transition: 'margin-right 0.3s ease-in-out',
          minHeight: '800px'
        }}>
          <DungeonContent
            message={message}
            setMessage={setMessage}
            loading={loading}
            error={error}
            dungeonResult={dungeonResult}
            parsedDungeonData={parsedDungeonData}
            selectedRoomId={selectedRoomId}
            showGrid={showGrid}
            setShowGrid={setShowGrid}
            onRoomSelect={handleRoomSelect}
            onSubmit={handleSubmit}
            onClear={clearHistory}
          />
        </Box>

        {/* Settings Sidebar */}
        <Box sx={{
          position: 'absolute',
          right: 0,
          top: 0,
          height: '100%',
          minHeight: '800px',
          zIndex: 1
        }}>
          <DungeonSidebar
            settings={settings}
            onSettingsChange={handleSettingsChange}
            expanded={settingsExpanded}
            onToggle={toggleSettings}
          />
        </Box>
      </Box>
    </Paper>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Simple Header */}
        <AppBar position="static" elevation={0} sx={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'primary.main', fontWeight: 700 }}>
              DungeonGen
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Main Dungeon Generator Interface */}
        <Box sx={{ flexGrow: 1, p: 3 }}>
          <Box sx={{ height: '100%', maxWidth: 'none' }}>
            <DungeonGenerator />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
