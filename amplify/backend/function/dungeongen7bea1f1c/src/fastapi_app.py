"""
FastAPI application for DungeonGen backend.
"""

import os
import sys
import traceback
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from api.auth.fastapi_router import auth_router
from api.generate.fastapi_router import generate_router

# Create FastAPI app
app = FastAPI(
    title="DungeonGen Backend API",
    description="AI-powered dungeon generation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS - permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(generate_router, prefix="/api/generate", tags=["generation"])

# Debug: Print all routes
print("FastAPI routes:")
for route in app.routes:
    if hasattr(route, "path") and hasattr(route, "methods"):
        print(f"  {route.methods} {route.path}")
    elif hasattr(route, "path"):
        print(f"  {route.path}")


@app.get("/")
async def home():
    """Get API information and available endpoints."""
    return {
        "message": "DungeonGen Backend API",
        "status": "running",
        "version": "1.0.0",
        "runtime": "fastapi",
        "endpoints": {
            "auth": "/api/auth/login",
            "generate": "/api/generate/dungeon",
            "generate_info": "/api/generate/info",
            "health": "/api/health",
            "docs": "/docs",
        },
    }


@app.get("/api/auth/test")
async def test_auth_route():
    """Test endpoint to verify auth routing is working."""
    return {"message": "Auth routing is working", "path": "/api/auth/test"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dungeongen-backend-fastapi",
        "runtime": "fastapi",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    # Extract exception information
    exc_type = type(exc).__name__
    exc_value = str(exc)

    # Get traceback
    tb_lines = traceback.format_exc().splitlines()

    # Create error response
    error_response = {
        "error": "Internal server error",
        "error_type": "internal_error",
        "status_code": 500,
        "details": f"{exc_type}: {exc_value}",
        "traceback": "\n".join(tb_lines),
        "timestamp": datetime.utcnow().isoformat(),
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_type": "http_error",
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
