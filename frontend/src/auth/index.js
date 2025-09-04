// Main auth exports
export { AuthProvider, useAuth } from './AuthContext';
export { default as AuthGuard } from './components/AuthGuard';
export { default as LoginPage } from './components/LoginPage';
export { default as LogoutButton } from './components/LogoutButton';

// Hook exports
export { useAuthHeaders, useAuthenticatedFetch } from './hooks/useAuth';
