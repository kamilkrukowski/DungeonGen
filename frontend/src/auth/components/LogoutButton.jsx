import React from 'react';
import { Button, IconButton, Tooltip } from '@mui/material';
import { Logout as LogoutIcon } from '@mui/icons-material';
import { useAuth } from '../AuthContext';

const LogoutButton = ({ variant = 'icon', size = 'small', ...props }) => {
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  if (variant === 'icon') {
    return (
      <Tooltip title="Logout">
        <IconButton
          onClick={handleLogout}
          size={size}
          sx={{ color: 'white' }}
          {...props}
        >
          <LogoutIcon />
        </IconButton>
      </Tooltip>
    );
  }

  return (
    <Button
      onClick={handleLogout}
      startIcon={<LogoutIcon />}
      variant="outlined"
      size={size}
      sx={{ color: 'white', borderColor: 'white' }}
      {...props}
    >
      Logout
    </Button>
  );
};

export default LogoutButton;
