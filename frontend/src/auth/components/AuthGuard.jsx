import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../AuthContext';
import LoginPage from './LoginPage';

const AuthGuard = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // If still loading (checking auth status on app start), show a minimal loading state
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <CircularProgress size={40} sx={{ color: 'white' }} />
      </Box>
    );
  }

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // If authenticated, render the protected content
  return children;
};

export default AuthGuard;
