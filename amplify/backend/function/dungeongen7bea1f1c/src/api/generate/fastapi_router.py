"""
FastAPI generate router for structured dungeon generation.
"""

import sys
import traceback
import unicodedata
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth.fastapi_router import get_current_user
from dungeon_core.dungeon.generator import DungeonGenerator
from dungeon_core.dungeon.utils import parse_user_guidelines
from models.dungeon import GenerationOptions
from utils import simple_trace

from .models import (
    DungeonGenerateRequest,
    DungeonGenerateResponse,
    ErrorLocation,
    ErrorResponse,
    ErrorType,
)

# Create router
generate_router = APIRouter()

# Initialize dungeon generator
dungeon_generator = DungeonGenerator()


def extract_exception_location(exc_info: tuple | None = None) -> dict[str, Any]:
    """
    Extract file and line number information from an exception.

    Args:
        exc_info: Exception info tuple (type, value, traceback)

    Returns:
        Dictionary with file, line, and function information
    """
    if exc_info is None:
        exc_info = sys.exc_info()

    if exc_info[2] is None:
        return {"file": "unknown", "line": None, "function": "unknown"}

    tb = exc_info[2]

    # Get the most recent frame (where the exception occurred)
    while tb.tb_next is not None:
        tb = tb.tb_next

    frame = tb.tb_frame
    filename = frame.f_code.co_filename
    lineno = tb.tb_lineno
    function = frame.f_code.co_name

    # Convert absolute paths to relative paths for better readability
    if filename.startswith("/"):
        # Try to find the project root and make path relative
        if "/backend/" in filename:
            filename = filename.split("/backend/")[-1]
        elif "/DungeonGen/" in filename:
            filename = filename.split("/DungeonGen/")[-1]

    # Validate that lineno is a valid integer
    try:
        line_number = int(lineno) if lineno is not None else None
    except (ValueError, TypeError):
        line_number = None

    return {"file": filename, "line": line_number, "function": function}


def create_error_response(
    error: str,
    error_type: ErrorType,
    status_code: int,
    details: str,
    exc_info: tuple | None = None,
    additional_context: str = "",
) -> ErrorResponse:
    """
    Create a comprehensive error response with location information.

    Args:
        error: Main error message
        error_type: Type of error
        status_code: HTTP status code
        details: Error details
        exc_info: Exception info tuple
        additional_context: Additional context information

    Returns:
        ErrorResponse object with enhanced debugging information
    """
    # Extract location information
    location_info = extract_exception_location(exc_info)

    # Get full traceback
    full_traceback = traceback.format_exc()

    # Build enhanced traceback with location info
    location_str = f"File: {location_info['file']}"
    if location_info["line"] is not None:
        location_str += f"\nLine: {location_info['line']}"
    else:
        location_str += "\nLine: unknown"
    location_str += f"\nFunction: {location_info['function']}"

    enhanced_traceback = f"""Error Location:
{location_str}

{additional_context}

Full Traceback:
{full_traceback}"""

    # Create location object for the response, handling None values gracefully
    try:
        location_obj = ErrorLocation(
            file=location_info["file"],
            line=location_info["line"],
            function=location_info["function"],
        )
    except Exception as e:
        # Fallback if location creation fails
        print(f"WARNING: Failed to create ErrorLocation: {e}")
        location_obj = None

    return ErrorResponse(
        error=error,
        error_type=error_type,
        status_code=status_code,
        details=details,
        traceback=enhanced_traceback,
        location=location_obj,
    )


@generate_router.post("/dungeon", response_model=DungeonGenerateResponse)
async def generate_structured_dungeon(
    request: DungeonGenerateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Generate a structured dungeon based on user guidelines."""
    try:
        # Ensure proper UTF-8 encoding for guidelines text
        try:
            # Validate and normalize UTF-8 encoding
            if isinstance(request.guidelines, str):
                # Ensure the string is properly encoded as UTF-8
                guidelines_text = request.guidelines.encode("utf-8").decode("utf-8")
                # Normalize unicode characters
                guidelines_text = unicodedata.normalize("NFC", guidelines_text)
            else:
                guidelines_text = str(request.guidelines)
        except UnicodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid text encoding: {str(e)}",
            )

        # Parse user guidelines into structured format
        guidelines = parse_user_guidelines(guidelines_text)

        # Create generation options
        options = GenerationOptions()
        if request.options:
            # Apply any custom options to guidelines
            for key, value in request.options.items():
                if hasattr(guidelines, key):
                    setattr(guidelines, key, value)
                elif hasattr(options, key):
                    setattr(options, key, value)

        # Generate dungeon using the generator
        try:
            result = dungeon_generator.generate_dungeon(guidelines, options)
        except Exception as e:
            print(f"ERROR: Dungeon generation failed with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Generation failed: {str(e)}",
            )

        # Check if generation failed and return appropriate status code
        if result.status == "error":
            # Determine the appropriate HTTP status code based on error types
            error_message = " ".join(result.errors).lower()

            # Check for API key errors first
            if any(
                keyword in error_message
                for keyword in [
                    "invalid api key",
                    "invalid_api_key",
                    "401",
                    "unauthorized",
                    "authentication",
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API Key - The GROQ API key is invalid or missing. Please check your API key configuration.",
                )
            # Check for connection/network errors
            elif any(
                keyword in error_message
                for keyword in [
                    "connection",
                    "timeout",
                    "network",
                    "unavailable",
                    "llm",
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Connection to AI service failed - Unable to connect to the AI model service. Please check your connection and try again.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Generation failed: {'; '.join(result.errors)}",
                )

        # Use Pydantic auto-serialization
        response_data = {
            "dungeon": result.dungeon.model_dump(),
            "guidelines": result.guidelines.model_dump(),
            "options": result.options.model_dump(),
            "generation_time": result.generation_time.isoformat(),
            "status": result.status,
            "errors": result.errors,
        }

        # Validate response using Pydantic model
        response = DungeonGenerateResponse(**response_data)
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {str(e)}",
        )


@generate_router.get("/info")
@simple_trace("get_generator_info")
async def get_generator_info(current_user: dict[str, Any] = Depends(get_current_user)):
    """Get information about the dungeon generator."""
    try:
        info = dungeon_generator.get_model_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get info: {str(e)}",
        )
