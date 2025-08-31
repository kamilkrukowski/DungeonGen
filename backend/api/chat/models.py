"""
Pydantic models for the chat endpoint.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat generation."""

    message: str = Field(
        ...,
        description="User's message for chat",
        min_length=1,
        max_length=1000,
        example="Create a haunted castle with ghostly encounters and hidden passages",
    )


class ChatResponse(BaseModel):
    """Response model for chat generation."""

    message: str = Field(..., description="Generated chat response")
    user_input: str = Field(..., description="Original user input")
    model: str = Field(..., description="AI model used for generation")
    status: str = Field(..., description="Generation status")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
