import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Build-time check for required environment variables
if (!import.meta.env.VITE_API_URL) {
  throw new Error('VITE_API_URL environment variable is required but not set!');
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
