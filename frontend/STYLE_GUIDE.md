# Frontend Style Guide

## Overview
This document outlines the coding standards, component patterns, and best practices for the DungeonGen React frontend application.

## Technology Stack
- **Framework**: React 18+ with Vite
- **UI Library**: Material-UI (MUI) v5
- **Styling**: Emotion (CSS-in-JS)
- **Package Manager**: npm
- **Development Server**: Vite Dev Server

## Project Structure
```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Page-level components
│   ├── hooks/         # Custom React hooks
│   ├── utils/         # Utility functions
│   ├── types/         # TypeScript type definitions
│   ├── constants/     # Application constants
│   └── assets/        # Static assets
├── public/            # Public assets
└── dist/              # Build output
```

## Component Guidelines

### 1. Component Structure
```tsx
import React from 'react';
import { Box, Typography } from '@mui/material';

interface ComponentProps {
  title: string;
  children?: React.ReactNode;
}

export const Component: React.FC<ComponentProps> = ({ title, children }) => {
  return (
    <Box>
      <Typography variant="h4">{title}</Typography>
      {children}
    </Box>
  );
};
```

### 2. Material-UI Usage
- Use MUI components as the primary UI building blocks
- Leverage the theme system for consistent styling
- Prefer `sx` prop for component-specific styles
- Use `styled` components for complex custom styling

### 3. Styling Patterns
```tsx
// Good: Using sx prop for component-specific styles
<Box sx={{
  display: 'flex',
  gap: 2,
  p: 2,
  backgroundColor: 'background.paper'
}}>

// Good: Using styled components for reusable styles
const StyledCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
}));
```

## Color Palette
Use the Material-UI theme colors:
- **Primary**: Blue (#1976d2)
- **Secondary**: Orange (#dc004e)
- **Error**: Red (#d32f2f)
- **Warning**: Amber (#ed6c02)
- **Info**: Light Blue (#0288d1)
- **Success**: Green (#2e7d32)

## Typography
Follow Material-UI typography variants:
- `h1` - Main page titles
- `h2` - Section headers
- `h3` - Subsection headers
- `h4` - Component titles
- `h5` - Small headers
- `h6` - Caption headers
- `body1` - Main text content
- `body2` - Secondary text
- `caption` - Small text/captions

## Spacing
Use Material-UI spacing system:
- `theme.spacing(1)` = 8px
- `theme.spacing(2)` = 16px
- `theme.spacing(3)` = 24px
- `theme.spacing(4)` = 32px

## Component Patterns

### 1. Layout Components
```tsx
// Page layout with consistent spacing
const PageLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Container maxWidth="lg" sx={{ py: 4 }}>
    {children}
  </Container>
);
```

### 2. Form Components
```tsx
// Consistent form field styling
const FormField: React.FC<{ label: string; children: React.ReactNode }> = ({
  label,
  children
}) => (
  <Box sx={{ mb: 2 }}>
    <Typography variant="body2" sx={{ mb: 1 }}>
      {label}
    </Typography>
    {children}
  </Box>
);
```

### 3. Card Components
```tsx
// Standard card layout
const ContentCard: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children
}) => (
  <Card sx={{ p: 3, mb: 2 }}>
    <Typography variant="h6" sx={{ mb: 2 }}>
      {title}
    </Typography>
    {children}
  </Card>
);
```

## State Management
- Use React hooks for local state
- Consider Context API for shared state
- Keep state as close to where it's used as possible
- Use custom hooks for complex state logic

## Error Handling
```tsx
// Error boundary pattern
const ErrorFallback: React.FC<{ error: Error }> = ({ error }) => (
  <Alert severity="error" sx={{ m: 2 }}>
    <AlertTitle>Error</AlertTitle>
    {error.message}
  </Alert>
);
```

## Loading States
```tsx
// Consistent loading pattern
const LoadingSpinner: React.FC = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
    <CircularProgress />
  </Box>
);
```

## Accessibility
- Use semantic HTML elements
- Include proper ARIA labels
- Ensure keyboard navigation
- Maintain color contrast ratios
- Use MUI's built-in accessibility features

## Performance
- Use React.memo for expensive components
- Implement proper dependency arrays in useEffect
- Lazy load components when appropriate
- Optimize bundle size with code splitting

## Testing
- Write unit tests for utility functions
- Test component rendering and interactions
- Use React Testing Library for component tests
- Mock external dependencies appropriately

## Code Quality
- Use TypeScript for type safety
- Follow ESLint rules
- Use Prettier for code formatting
- Write meaningful component and function names
- Add JSDoc comments for complex functions

## File Naming
- Use PascalCase for component files: `UserProfile.tsx`
- Use camelCase for utility files: `formatDate.ts`
- Use kebab-case for asset files: `hero-image.png`

## Import Organization
```tsx
// 1. React imports
import React from 'react';

// 2. Third-party libraries
import { Box, Typography } from '@mui/material';

// 3. Local imports
import { UserProfile } from './UserProfile';
import { formatDate } from '../utils/formatDate';
```

## Git Commit Messages
- Use conventional commits format
- Be descriptive and concise
- Reference issue numbers when applicable

Example:
```
feat: add user profile component
fix: resolve navigation bug in mobile view
docs: update README with setup instructions
```
