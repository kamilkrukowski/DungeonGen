import React from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Typography,
  Collapse,
} from '@mui/material';
import {
  Error as ErrorIcon,
  WifiOff as ConnectionIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const ErrorBanner = ({ error, onRetry, onDismiss }) => {
  const isConnectionError = error?.toLowerCase().includes('connection') ||
                           error?.toLowerCase().includes('llm provider') ||
                           error?.toLowerCase().includes('ai service');

  const getErrorIcon = () => {
    if (isConnectionError) return <ConnectionIcon />;
    return <ErrorIcon />;
  };

  const getErrorTitle = () => {
    if (isConnectionError) return 'Connection Failed';
    return 'Generation Failed';
  };

  const getErrorMessage = () => {
    if (isConnectionError) {
      return 'Unable to connect to the AI model service. This could be due to network issues or the service being temporarily unavailable.';
    }
    return error || 'An unexpected error occurred during dungeon generation.';
  };

  const getErrorSeverity = () => {
    if (isConnectionError) return 'warning';
    return 'error';
  };

  const getActionButtons = () => {
    const buttons = [];

    if (onRetry) {
      buttons.push(
        <Button
          key="retry"
          color="inherit"
          size="small"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          sx={{ mr: 1 }}
        >
          Try Again
        </Button>
      );
    }

    if (onDismiss) {
      buttons.push(
        <Button
          key="dismiss"
          color="inherit"
          size="small"
          onClick={onDismiss}
        >
          Dismiss
        </Button>
      );
    }

    return buttons;
  };

  return (
    <Collapse in={!!error}>
      <Alert
        severity={getErrorSeverity()}
        icon={getErrorIcon()}
        action={getActionButtons()}
        sx={{
          mb: 2,
          '& .MuiAlert-message': {
            width: '100%',
          },
        }}
      >
        <AlertTitle sx={{ fontWeight: 600 }}>
          {getErrorTitle()}
        </AlertTitle>

        <Typography variant="body2" sx={{ mb: 1 }}>
          {getErrorMessage()}
        </Typography>

        {isConnectionError && (
          <Box sx={{ mt: 1, p: 1, backgroundColor: 'rgba(255, 193, 7, 0.1)', borderRadius: 1 }}>
            <Typography variant="caption" display="flex" alignItems="center" sx={{ color: 'text.secondary' }}>
              <InfoIcon sx={{ fontSize: 16, mr: 0.5 }} />
              <strong>Tip:</strong> Check your internet connection and try again. If the problem persists, the AI service may be temporarily unavailable.
            </Typography>
          </Box>
        )}
      </Alert>
    </Collapse>
  );
};

export default ErrorBanner;
