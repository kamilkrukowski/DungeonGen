# DungeonGen

A modern full-stack application for dungeon generation, built with React frontend and Flask backend.

## 🏗️ Project Structure

```
DungeonGen/
├── frontend/           # React application with Vite
│   ├── src/           # Source code
│   ├── public/        # Public assets
│   ├── Dockerfile     # Frontend container configuration
│   └── STYLE_GUIDE.md # Frontend development guidelines
├── backend/           # Flask API
│   ├── app.py         # Main Flask application
│   ├── pyproject.toml # UV project configuration
│   └── Dockerfile     # Backend container configuration
├── docker-compose.yml # Multi-container orchestration
├── .env              # Environment variables
└── README.md         # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- UV package manager (for Python)

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DungeonGen
   ```

2. **Start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Health Check: http://localhost:8000/api/health
   - Jaeger UI: http://localhost:16686

### Local Development

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Backend Setup
```bash
cd backend
uv sync
uv run python app.py
```

## 🛠️ Technology Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Material-UI (MUI)** - Component library
- **Emotion** - CSS-in-JS styling

### Backend
- **Flask** - Python web framework
- **Flask-CORS** - Cross-origin resource sharing
- **UV** - Fast Python package manager
- **python-dotenv** - Environment variable management
- **Jaeger Client** - Distributed tracing
- **Flask-OpenTracing** - OpenTracing integration for Flask

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Jaeger** - Distributed tracing and monitoring

## 📁 Development Guidelines

### Frontend
- Follow the [Style Guide](frontend/STYLE_GUIDE.md) for component patterns
- Use Material-UI components for consistent UI
- Implement proper TypeScript types
- Follow React best practices

### Backend
- Use UV for dependency management
- Follow Flask application factory pattern
- Implement proper error handling
- Use environment variables for configuration

## 🔧 Configuration

### Environment Variables
The `.env` file contains configuration for the backend:
- `FLASK_ENV` - Flask environment (development/production)
- `PORT` - Backend server port
- `DATABASE_URL` - Database connection string
- `API_SECRET_KEY` - Secret key for API authentication
- `CORS_ORIGINS` - Allowed CORS origins
- `JAEGER_AGENT_HOST` - Jaeger agent hostname
- `JAEGER_AGENT_PORT` - Jaeger agent port
- `JAEGER_ENDPOINT` - Jaeger collector endpoint
- `JAEGER_SERVICE_NAME` - Service name for tracing

### Docker Configuration
- Frontend runs on port 3000
- Backend runs on port 8000 (mapped from container port 5000)
- Jaeger UI runs on port 16686
- All services are connected via Docker network
- Volume mounts enable hot reloading during development

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
npm run test
```

### Backend Testing
```bash
cd backend
uv run pytest
```

## 🔧 Code Quality

### Pre-commit Hooks
The project uses pre-commit hooks to ensure code quality:

#### Setup
```bash
# Install pre-commit hooks (already done during setup)
pre-commit install

# Run hooks on all files
pre-commit run --all-files

# Run hooks on staged files only
pre-commit run
```

#### Available Hooks
- **Ruff** - Fast Python linter and formatter
- **Black** - Python code formatter
- **Pre-commit hooks** - General file checks (trailing whitespace, YAML validation, etc.)

#### Configuration
- Ruff configuration: `backend/pyproject.toml`
- Black configuration: `backend/pyproject.toml`
- Pre-commit configuration: `.pre-commit-config.yaml`

#### Manual Formatting
```bash
# Format Python code with Black
cd backend
uv run black .

# Lint Python code with Ruff
cd backend
uv run ruff check .
uv run ruff format .
```

## 🔍 Distributed Tracing

The application includes Jaeger distributed tracing for monitoring and debugging:

### Accessing Jaeger UI
- **URL**: http://localhost:16686
- **Service**: `dungeongen-backend`

### Testing Tracing
1. Start the application with `docker-compose up --build`
2. Access the Jaeger UI at http://localhost:16686
3. Make requests to the backend API endpoints
4. View traces in the Jaeger UI

### Trace Endpoints
- `/` - Home endpoint with tracing
- `/api/health` - Health check with tracing
- `/api/trace-test` - Test endpoint with simulated work

### Tracing Configuration
The backend automatically traces all requests and includes:
- Request method and endpoint
- Response status codes
- Custom spans for specific operations
- Service name and tags

## 📦 Building for Production

### Frontend Build
```bash
cd frontend
npm run build
```

### Docker Production Build
```bash
docker-compose -f docker-compose.prod.yml up --build
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the style guides
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions and support:
- Check the documentation in each folder
- Review the style guides
- Open an issue on GitHub
