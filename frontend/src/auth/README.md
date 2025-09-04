# Authentication Module

This module provides JWT-based authentication for the DungeonGen frontend application.

## Structure

```
auth/
├── AuthContext.jsx          # Main authentication context and provider
├── components/
│   ├── AuthGuard.jsx        # Route protection component
│   ├── LoginPage.jsx        # Login form component
│   └── LogoutButton.jsx     # Logout button component
├── hooks/
│   └── useAuth.js           # Authentication hooks
├── index.js                 # Module exports
└── README.md               # This file
```

## Components

### AuthProvider
- Provides authentication context to the entire app
- Manages JWT token storage and validation
- Handles login/logout operations

### AuthGuard
- Protects routes by checking authentication status
- Shows login page if not authenticated
- Shows loading spinner while checking auth status

### LoginPage
- Simple password-only login form
- Handles login API calls
- Shows error messages for failed attempts

### LogoutButton
- Provides logout functionality
- Available as icon or button variant

## Hooks

### useAuth()
- Main authentication hook
- Returns: `{ isAuthenticated, isLoading, token, login, logout, getAuthHeaders }`

### useAuthHeaders()
- Returns authentication headers for API calls

### useAuthenticatedFetch()
- Returns a fetch function that automatically includes auth headers

## Usage

```jsx
import { AuthProvider, AuthGuard, useAuth } from './auth';

// Wrap your app with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AuthGuard>
        {/* Your protected content */}
      </AuthGuard>
    </AuthProvider>
  );
}

// Use authentication in components
function MyComponent() {
  const { isAuthenticated, login, logout } = useAuth();
  // ...
}
```

## API Integration

The authentication system expects the backend to provide:
- `POST /api/auth/login` - Login endpoint that accepts `{ password }` and returns `{ token }`
- JWT tokens in API responses
- Protected endpoints that require `Authorization: Bearer <token>` header

## Features

- ✅ JWT token storage in localStorage
- ✅ Automatic token expiration checking
- ✅ Route protection with AuthGuard
- ✅ Password-only login
- ✅ Authenticated API calls
- ✅ Logout functionality
- ✅ Loading states
- ✅ Error handling
