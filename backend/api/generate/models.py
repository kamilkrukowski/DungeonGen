"""
Pydantic models for the generate endpoint.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    """Types of errors that can occur during generation."""

    VALIDATION_ERROR = "validation_error"
    CONNECTION_ERROR = "connection_error"
    GENERATION_ERROR = "generation_error"
    INTERNAL_ERROR = "internal_error"
    INVALID_API_KEY = "invalid_api_key"


class DungeonGenerateRequest(BaseModel):
    """Request model for structured dungeon generation."""

    guidelines: str = Field(
        ...,
        description="User's description of the desired dungeon",
        min_length=1,
        max_length=1000,
        example="Create a haunted castle with ghostly encounters and hidden passages",
    )
    options: dict[str, Any] | None = Field(
        default=None, description="Optional generation parameters"
    )


class DungeonGenerateResponse(BaseModel):
    """Response model for structured dungeon generation."""

    dungeon: dict[str, Any] = Field(..., description="Generated dungeon data")
    guidelines: dict[str, Any] = Field(..., description="Parsed guidelines")
    options: dict[str, Any] = Field(..., description="Generation options used")
    generation_time: str = Field(..., description="Generation timestamp")
    status: str = Field(..., description="Generation status")
    errors: list = Field(default_factory=list, description="Any errors encountered")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    error_type: ErrorType = Field(..., description="Type of error")
    status_code: int = Field(..., description="HTTP status code")
    details: str | None = Field(None, description="Additional error details")
    traceback: str | None = Field(
        None, description="Full error traceback for debugging"
    )
