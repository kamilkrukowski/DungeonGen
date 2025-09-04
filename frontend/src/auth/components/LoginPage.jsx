import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Paper,
  IconButton,
  InputAdornment,
} from '@mui/material';
import { Lock as LockIcon, Castle as CastleIcon, Visibility, VisibilityOff } from '@mui/icons-material';
import { useAuth } from '../AuthContext';

const LoginPage = () => {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(() => {
    // Initialize error state from localStorage to persist across remounts
    return localStorage.getItem('loginError') || '';
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const errorRef = useRef('');
  const isInitialMount = useRef(true);

  // Effect to manage error state persistence
  useEffect(() => {
    errorRef.current = error;

    // Don't remove error from localStorage on initial mount if it's empty
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    // Only store error in localStorage if it's not already there
    if (error) {
      const storedError = localStorage.getItem('loginError');
      if (storedError !== error) {
        localStorage.setItem('loginError', error);
      }
    } else {
      // Only remove from localStorage if we're not in the middle of a login attempt
      if (!isSubmitting) {
        localStorage.removeItem('loginError');
      }
    }
  }, [error, isSubmitting]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Clear error from localStorage when component unmounts (e.g., successful login)
      localStorage.removeItem('loginError');
    };
  }, []);

  const handlePasswordChange = (e) => {
    setPassword(e.target.value);
    // Don't clear error automatically - let user see it until they submit again
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!password.trim()) {
      setError('Please enter a password');
      return;
    }

    setIsSubmitting(true);
    setError('');
    localStorage.removeItem('loginError');

    try {
      const result = await login(password);

      if (!result.success) {
        const errorMessage = result.error || 'Login failed';

        // Store error in localStorage immediately
        localStorage.setItem('loginError', errorMessage);

        // Set error state
        setError(errorMessage);
      }
      // If successful, the AuthContext will handle the state change
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Paper
          elevation={10}
          sx={{
            width: '100%',
            maxWidth: 400,
            borderRadius: 3,
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              background: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
              color: 'white',
              p: 3,
              textAlign: 'center',
            }}
          >
            <CastleIcon sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
              DungeonGen
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9, mt: 1 }}>
              Enter your password to access the dungeon generator
            </Typography>
          </Box>

          {/* Login Form */}
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={handleSubmit}>
              {/* Hidden username field for accessibility */}
              <input
                type="text"
                name="username"
                autoComplete="username"
                style={{ display: 'none' }}
                tabIndex={-1}
                aria-hidden="true"
              />
              <TextField
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="Password"
                value={password}
                onChange={handlePasswordChange}
                disabled={isSubmitting}
                error={!!error}
                autoComplete="new-password"
                InputProps={{
                  startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleTogglePasswordVisibility}
                        onMouseDown={(e) => e.preventDefault()}
                        edge="end"
                        disabled={isSubmitting}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 3 }}
                autoFocus
              />

              {error && (
                <Alert
                  severity="error"
                  sx={{
                    mb: 3,
                    borderRadius: 2,
                    boxShadow: 3,
                    border: '2px solid',
                    borderColor: 'error.main',
                    backgroundColor: 'error.light',
                    animation: 'shake 0.5s ease-in-out',
                    '& .MuiAlert-icon': {
                      fontSize: '1.5rem'
                    },
                    '& .MuiAlert-message': {
                      fontSize: '1.1rem',
                      fontWeight: 600
                    },
                    '@keyframes shake': {
                      '0%, 100%': { transform: 'translateX(0)' },
                      '25%': { transform: 'translateX(-5px)' },
                      '75%': { transform: 'translateX(5px)' }
                    }
                  }}
                >
                  {error}
                </Alert>
              )}

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={isSubmitting || !password.trim()}
                startIcon={isSubmitting ? <CircularProgress size={20} /> : <LockIcon />}
                sx={{
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                  },
                }}
              >
                {isSubmitting ? 'Signing In...' : 'Sign In'}
              </Button>
            </form>
          </CardContent>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;
