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
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Divider from '@mui/material/Divider'
import TextField from '@mui/material/TextField'
import Fab from '@mui/material/Fab'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import AutoAwesome from '@mui/icons-material/AutoAwesome'
import Psychology from '@mui/icons-material/Psychology'
import Speed from '@mui/icons-material/Speed'
import Security from '@mui/icons-material/Security'
import PlayArrow from '@mui/icons-material/PlayArrow'
import GitHub from '@mui/icons-material/GitHub'
import Description from '@mui/icons-material/Description'
import Chat from '@mui/icons-material/Chat'
import Send from '@mui/icons-material/Send'
import Close from '@mui/icons-material/Close'
import './App.css'

// Create a custom theme with dungeon-inspired colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#2c3e50',
      dark: '#1a252f',
    },
    secondary: {
      main: '#e74c3c',
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = message.trim();
    setLoading(true);
    setError('');

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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/generate`, {
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

  const clearHistory = () => {
    setChatHistory([]);
    setError('');
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          minHeight: '70vh',
          maxHeight: '80vh',
        }
      }}
    >
      <DialogTitle sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <Typography variant="h6">
          <Chat sx={{ mr: 1, verticalAlign: 'middle' }} />
          Dungeon Generator Chat
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            onClick={clearHistory}
            sx={{ color: 'white', fontSize: '0.8rem' }}
            size="small"
          >
            Clear History
          </Button>
          <Button onClick={onClose} sx={{ color: 'white' }}>
            <Close />
          </Button>
        </Stack>
      </DialogTitle>

      <DialogContent sx={{ p: 3, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
          Describe the type of dungeon you want to generate. Be specific about themes, challenges, or special features!
        </Typography>

        {/* Chat History */}
        <Box sx={{
          flexGrow: 1,
          mb: 3,
          overflowY: 'auto',
          maxHeight: '400px',
          border: '1px solid #e0e0e0',
          borderRadius: 2,
          p: 2,
          backgroundColor: '#fafafa'
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

          <Button
            type="submit"
            variant="contained"
            disabled={loading || !message.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <Send />}
            fullWidth
          >
            {loading ? 'Generating...' : 'Generate Dungeon'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function App() {
  const [count, setCount] = useState(0)
  const [chatOpen, setChatOpen] = useState(false)

  const features = [
    {
      icon: <AutoAwesome sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'AI-Powered Generation',
      description: 'Advanced algorithms create unique and challenging dungeon layouts automatically.'
    },
    {
      icon: <Psychology sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Smart Design',
      description: 'Intelligent room placement and pathfinding for realistic dungeon structures.'
    },
    {
      icon: <Speed sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Lightning Fast',
      description: 'Generate complex dungeons in seconds with our optimized algorithms.'
    },
    {
      icon: <Security sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Secure & Reliable',
      description: 'Built with modern security practices and robust error handling.'
    }
  ]

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        {/* Navigation */}
        <AppBar position="static" elevation={0} sx={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'primary.main', fontWeight: 700 }}>
              DungeonGen
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button color="inherit" sx={{ color: 'text.primary' }}>
                Features
              </Button>
              <Button color="inherit" sx={{ color: 'text.primary' }}>
                Documentation
              </Button>
              <Button variant="contained" color="primary">
                Get Started
              </Button>
            </Stack>
          </Toolbar>
        </AppBar>

        {/* Hero Section */}
        <Box
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            py: 12,
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <Container maxWidth="lg">
            <Grid container spacing={6} alignItems="center">
              <Grid item xs={12} md={6}>
                <Typography variant="h1" gutterBottom sx={{ color: 'white' }}>
                  Generate Amazing Dungeons
                </Typography>
                <Typography variant="h5" paragraph sx={{ color: 'rgba(255,255,255,0.9)', mb: 4 }}>
                  Create unique, challenging, and immersive dungeon layouts with our AI-powered generation system.
                  Perfect for game developers, DMs, and creative storytellers.
                </Typography>
                <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', gap: 2 }}>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<PlayArrow />}
                    onClick={() => setChatOpen(true)}
                    sx={{
                      backgroundColor: 'white',
                      color: 'primary.main',
                      '&:hover': {
                        backgroundColor: 'rgba(255,255,255,0.9)',
                      }
                    }}
                  >
                    Try Demo
                  </Button>
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<GitHub />}
                    sx={{
                      borderColor: 'white',
                      color: 'white',
                      '&:hover': {
                        borderColor: 'rgba(255,255,255,0.8)',
                        backgroundColor: 'rgba(255,255,255,0.1)',
                      }
                    }}
                  >
                    View Source
                  </Button>
                </Stack>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box
                  sx={{
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: 4,
                    p: 4,
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)'
                  }}
                >
                  <Typography variant="h4" gutterBottom align="center">
                    Live Preview
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                    <Card sx={{ minWidth: 275, maxWidth: 400, backgroundColor: 'rgba(255,255,255,0.9)' }}>
                      <CardContent>
                        <Typography variant="h6" component="h2" gutterBottom color="primary.main">
                          Interactive Demo
                        </Typography>
                        <Typography variant="body1" color="text.secondary" paragraph>
                          Experience the power of DungeonGen with our interactive demo.
                          Generate dungeons in real-time and see the magic happen.
                        </Typography>

                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                          <Button
                            variant="contained"
                            onClick={() => setCount((count) => count + 1)}
                            sx={{ mr: 2 }}
                          >
                            Generate ({count})
                          </Button>
                          <Button
                            variant="outlined"
                            onClick={() => setCount(0)}
                          >
                            Reset
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Container>
        </Box>

        {/* Features Section */}
        <Container maxWidth="lg" sx={{ py: 8 }}>
          <Typography variant="h2" component="h2" gutterBottom align="center" sx={{ mb: 6 }}>
            Why Choose DungeonGen?
          </Typography>

          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card sx={{ height: '100%', textAlign: 'center', p: 3 }}>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" component="h3" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {feature.description}
                  </Typography>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>

        {/* CTA Section */}
        <Box sx={{ backgroundColor: 'background.paper', py: 8 }}>
          <Container maxWidth="md">
            <Paper
              elevation={0}
              sx={{
                p: 6,
                textAlign: 'center',
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                color: 'white',
                borderRadius: 4
              }}
            >
              <Typography variant="h3" gutterBottom>
                Ready to Create Amazing Dungeons?
              </Typography>
              <Typography variant="h6" paragraph sx={{ color: 'rgba(255,255,255,0.9)', mb: 4 }}>
                Join thousands of developers and creators who are already using DungeonGen
                to bring their worlds to life.
              </Typography>
              <Stack direction="row" spacing={2} justifyContent="center" sx={{ flexWrap: 'wrap', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<PlayArrow />}
                  onClick={() => setChatOpen(true)}
                  sx={{
                    backgroundColor: 'white',
                    color: 'primary.main',
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.9)',
                    }
                  }}
                >
                  Start Creating
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<Description />}
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'rgba(255,255,255,0.8)',
                      backgroundColor: 'rgba(255,255,255,0.1)',
                    }
                  }}
                >
                  Read Docs
                </Button>
              </Stack>
            </Paper>
          </Container>
        </Box>

        {/* Footer */}
        <Box sx={{ backgroundColor: 'primary.dark', color: 'white', py: 4 }}>
          <Container maxWidth="lg">
            <Grid container spacing={4}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  DungeonGen
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  The ultimate tool for generating unique and challenging dungeon layouts.
                  Built with modern technologies and designed for creators.
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Quick Links
                </Typography>
                <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', gap: 1 }}>
                  <Button size="small" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    Features
                  </Button>
                  <Button size="small" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    Documentation
                  </Button>
                  <Button size="small" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    GitHub
                  </Button>
                  <Button size="small" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    Contact
                  </Button>
                </Stack>
              </Grid>
            </Grid>
            <Divider sx={{ my: 3, borderColor: 'rgba(255,255,255,0.2)' }} />
            <Typography variant="body2" align="center" sx={{ color: 'rgba(255,255,255,0.5)' }}>
              © 2024 DungeonGen. Built with React, Vite, and Material-UI.
            </Typography>
          </Container>
        </Box>

        {/* Floating Chat Button */}
        <Fab
          color="primary"
          aria-label="chat"
          onClick={() => setChatOpen(true)}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            backgroundColor: 'secondary.main',
            '&:hover': {
              backgroundColor: 'secondary.dark',
            }
          }}
        >
          <Chat />
        </Fab>

        {/* Chat Dialog */}
        <ChatComponent open={chatOpen} onClose={() => setChatOpen(false)} />
      </Box>
    </ThemeProvider>
  )
}

export default App
