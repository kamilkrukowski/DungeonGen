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
import Chat from '@mui/icons-material/Chat'
import Send from '@mui/icons-material/Send'
import Castle from '@mui/icons-material/Castle'
import GridViewIcon from '@mui/icons-material/GridView'
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

// Chat Component
function ChatComponent({ open, onClose }) {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dungeonResult, setDungeonResult] = useState(null);
  const [parsedDungeonData, setParsedDungeonData] = useState(null);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [showGrid, setShowGrid] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = message.trim();
    setLoading(true);
    setError('');
    setDungeonResult(null);
    setParsedDungeonData(null);

    // Add user message to chat history
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setChatHistory(prev => [...prev, newUserMessage]);
    setMessage(''); // Clear input immediately

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();

      if (response.ok) {
        // Add AI response to chat history
        const newAiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.message,
          timestamp: new Date().toLocaleTimeString()
        };
        setChatHistory(prev => [...prev, newAiMessage]);
      } else {
        setError(data.error || 'Failed to generate dungeon');
        // Remove the user message if there was an error
        setChatHistory(prev => prev.filter(msg => msg.id !== newUserMessage.id));
      }
    } catch (err) {
      setError('Network error. Please check if the backend is running.');
      // Remove the user message if there was an error
      setChatHistory(prev => prev.filter(msg => msg.id !== newUserMessage.id));
    } finally {
      setLoading(false);
    }
  };

  const handleDungeonGenerate = async () => {
    if (!message.trim()) return;

    const userMessage = message.trim();
    setLoading(true);
    setError('');
    setDungeonResult(null);
    setParsedDungeonData(null);

    try {
      // Create structured dungeon generation request
      const dungeonRequest = {
        guidelines: userMessage,
        options: {
          room_count: 10,
          layout_type: "poisson_disc"
        }
      };

      // Debug: Log what we're sending
      console.log('Frontend sending dungeon request:', dungeonRequest);
      console.log('Frontend sending JSON payload:', JSON.stringify(dungeonRequest, null, 2));

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/generate/dungeon`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dungeonRequest),
      });

      const data = await response.json();
      console.log('Frontend received response:', data);

      if (response.ok) {
        setDungeonResult(data);

        // Parse the dungeon data
        try {
          const parsed = parseDungeonData(data);
          setParsedDungeonData(parsed);
          setShowGrid(true);
        } catch (parseError) {
          console.error('Error parsing dungeon data:', parseError);
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
    setChatHistory([]);
    setError('');
    setDungeonResult(null);
    setParsedDungeonData(null);
    setShowGrid(false);
    setSelectedRoomId(null);
  };

  const handleRoomSelect = (room) => {
    setSelectedRoomId(room.id);
  };

  return (
    <Paper sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      borderRadius: 3,
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Box sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        p: 2
      }}>
        <Typography variant="h6">
          <Chat sx={{ mr: 1, verticalAlign: 'middle' }} />
          Dungeon Generator Chat
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
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
            Clear History
          </Button>
        </Box>
      </Box>

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
                  onRoomSelect={handleRoomSelect}
                  selectedRoomId={selectedRoomId}
                />
              </Box>
              {selectedRoomId && (
                <Box sx={{ mt: 2, p: 2, backgroundColor: 'white', borderRadius: 1 }}>
                  {parsedDungeonData && parsedDungeonData.dungeon && (() => {
                    const selectedRoom = parsedDungeonData.dungeon.rooms.find(room => room.id === selectedRoomId);
                    const roomContent = parsedDungeonData.dungeon.getRoomContent(selectedRoomId);

                    return selectedRoom ? (
                      <>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                          Selected Room: {selectedRoom.name}
                        </Typography>
                        {selectedRoom.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            {selectedRoom.description}
                          </Typography>
                        )}
                        {roomContent && (
                          <>
                            {roomContent.atmosphere && (
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                <strong>Atmosphere:</strong> {roomContent.atmosphere}
                              </Typography>
                            )}
                            {roomContent.treasures && roomContent.treasures.length > 0 && (
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                <strong>Treasures:</strong> {roomContent.treasures.join(', ')}
                              </Typography>
                            )}
                          </>
                        )}
                      </>
                    ) : (
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Selected Room: {selectedRoomId}
                      </Typography>
                    );
                  })()}
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Chat History */}
        <Box sx={{
          flexGrow: 1,
          mb: 3,
          overflowY: 'auto',
          border: '1px solid #e0e0e0',
          borderRadius: 2,
          p: 2,
          backgroundColor: '#fafafa',
          minHeight: showGrid ? '200px' : '300px'
        }}>
          {chatHistory.length === 0 ? (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
              No messages yet. Start a conversation by describing your dungeon!
            </Typography>
          ) : (
            <Stack spacing={2}>
              {chatHistory.map((msg) => (
                <Box
                  key={msg.id}
                  sx={{
                    display: 'flex',
                    justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
                    mb: 1
                  }}
                >
                  <Card
                    sx={{
                      maxWidth: '80%',
                      backgroundColor: msg.type === 'user' ? 'primary.main' : 'white',
                      color: msg.type === 'user' ? 'white' : 'text.primary',
                      border: msg.type === 'ai' ? '1px solid #e0e0e0' : 'none',
                    }}
                  >
                    <CardContent sx={{ py: 1.5, px: 2 }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                        {msg.content}
                      </Typography>
                      <Typography variant="caption" sx={{ opacity: 0.7 }}>
                        {msg.timestamp}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              ))}
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <Card sx={{ backgroundColor: 'white', border: '1px solid #e0e0e0' }}>
                    <CardContent sx={{ py: 1.5, px: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2">Generating dungeon...</Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </Stack>
          )}
        </Box>

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
        <form onSubmit={handleSubmit}>
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

          {/* Split Button Layout */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={loading || !message.trim()}
              startIcon={loading ? <CircularProgress size={20} /> : <Send />}
              sx={{ flex: 1 }}
            >
              {loading ? 'Generating...' : 'Chat'}
            </Button>

            <Button
              variant="contained"
              color="secondary"
              disabled={loading || !message.trim()}
              startIcon={loading ? <CircularProgress size={20} /> : <Castle />}
              onClick={handleDungeonGenerate}
              sx={{ flex: 1 }}
            >
              {loading ? 'Generating...' : 'Dungeon'}
            </Button>
          </Box>
        </form>
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

        {/* Main Chat Interface */}
        <Box sx={{ flexGrow: 1, p: 3 }}>
          <Container maxWidth="md" sx={{ height: '100%' }}>
            <ChatComponent open={true} onClose={() => {}} />
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
