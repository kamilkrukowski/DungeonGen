"""
Authentication models for the DungeonGen API.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request model for user login."""

    password: str = Field(..., description="Admin password", min_length=1)


class LoginResponse(BaseModel):
    """Response model for successful login."""

    token: str = Field(..., description="JWT access token")
    message: str = Field(default="Login successful", description="Success message")


class AuthErrorResponse(BaseModel):
    """Error response model for authentication failures."""

    error: str = Field(..., description="Error message")
    error_type: str = Field(default="authentication_error", description="Error type")
    status_code: int = Field(default=401, description="HTTP status code")
