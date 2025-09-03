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
  // Handle both string errors and structured error objects
  const errorMessage = typeof error === 'string' ? error : error?.details || error?.error || 'Unknown error';
  const errorTraceback = error?.traceback;

  const isConnectionError = errorMessage?.toLowerCase().includes('connection') ||
                           errorMessage?.toLowerCase().includes('llm provider') ||
                           errorMessage?.toLowerCase().includes('ai service');

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
    return errorMessage || 'An unexpected error occurred during dungeon generation.';
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

        {/* Show traceback for debugging if available */}
        {errorTraceback && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
              Debug Information (click to expand):
            </Typography>
            <Box
              component="pre"
              sx={{
                mt: 1,
                p: 1,
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                borderRadius: 1,
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                maxHeight: '200px',
                overflow: 'auto',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                },
              }}
              onClick={(e) => {
                const target = e.target;
                if (target.style.maxHeight === '200px') {
                  target.style.maxHeight = 'none';
                } else {
                  target.style.maxHeight = '200px';
                }
              }}
              title="Click to expand/collapse traceback"
            >
              {errorTraceback}
            </Box>
          </Box>
        )}
      </Alert>
    </Collapse>
  );
};

export default ErrorBanner;
