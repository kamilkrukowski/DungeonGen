"""
Pydantic models for the generate endpoint.
"""

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request model for dungeon generation."""

    message: str = Field(
        ...,
        description="User's description of the desired dungeon",
        min_length=1,
        max_length=1000,
        example="Create a haunted castle with ghostly encounters and hidden passages",
    )


class GenerateResponse(BaseModel):
    """Response model for dungeon generation."""

    message: str = Field(..., description="Generated dungeon description")
    user_input: str = Field(..., description="Original user input")
    model: str = Field(..., description="AI model used for generation")
    status: str = Field(..., description="Generation status")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
