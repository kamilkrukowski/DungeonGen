"""
Generate endpoint router for structured dungeon generation.
"""

import json
import sys
import traceback

from flask import Blueprint, jsonify, request
from flask_restx import Namespace, Resource, fields

from api.auth.utils import require_auth

# Import for structured generation
from models.dungeon import GenerationOptions
from src.dungeon.generator import DungeonGenerator
from src.dungeon.utils import parse_user_guidelines
from utils import simple_trace

from .models import DungeonGenerateRequest, DungeonGenerateResponse, ErrorResponse

# Create blueprint for backward compatibility
generate_bp = Blueprint("generate", __name__, url_prefix="/api/generate")

# Initialize dungeon generator
dungeon_generator = DungeonGenerator()

# Create namespace for Flask-RESTX
generate_ns = Namespace(
    "generate", description="Structured dungeon generation operations"
)

error_model = generate_ns.model(
    "Error", {"error": fields.String(description="Error message")}
)

# Define models for structured dungeon generation
dungeon_generate_request_model = generate_ns.model(
    "DungeonGenerateRequest",
    {
        "guidelines": fields.String(
            required=True,
            description="User description of the desired dungeon",
            example="Create a haunted castle with ghostly encounters and hidden passages",
        ),
        "options": fields.Raw(
            required=False, description="Optional generation parameters"
        ),
    },
)

dungeon_generate_response_model = generate_ns.model(
    "DungeonGenerateResponse",
    {
        "dungeon": fields.Raw(description="Generated dungeon data"),
        "guidelines": fields.Raw(description="Parsed guidelines"),
        "options": fields.Raw(description="Generation options used"),
        "generation_time": fields.String(description="Generation timestamp"),
        "status": fields.String(description="Generation status"),
        "errors": fields.List(fields.String, description="Any errors encountered"),
    },
)

generator_info_model = generate_ns.model(
    "GeneratorInfo",
    {
        "model_name": fields.String(description="Name of the AI model"),
        "model_version": fields.String(description="Version of the model"),
        "capabilities": fields.List(fields.String, description="Model capabilities"),
        "max_tokens": fields.Integer(description="Maximum tokens for generation"),
    },
)


def extract_exception_location(exc_info: tuple | None = None) -> dict:
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
    error_type: str,
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
    from .models import ErrorLocation

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


@generate_ns.route("/dungeon")
class GenerateStructuredDungeon(Resource):
    @generate_ns.doc("generate_structured_dungeon")
    @generate_ns.expect(dungeon_generate_request_model)
    @generate_ns.response(200, "Success", dungeon_generate_response_model)
    @generate_ns.response(400, "Bad Request", error_model)
    @generate_ns.response(401, "Unauthorized", error_model)
    @generate_ns.response(500, "Internal Server Error", error_model)
    @simple_trace("generate_structured_dungeon")
    @require_auth
    def post(self):
        """Generate a structured dungeon based on user guidelines."""
        try:
            # Get current span to add attributes
            from opentelemetry import trace

            current_span = trace.get_current_span()

            # Validate request data
            data = request.get_json()
            if not data:
                return (
                    create_error_response(
                        error="No JSON data provided",
                        error_type="validation_error",
                        status_code=400,
                        details="Request body is empty or not valid JSON",
                        additional_context="Request validation failed at input parsing stage",
                    ).dict(),
                    400,
                )

            # Validate request using Pydantic model
            try:
                dungeon_request = DungeonGenerateRequest(**data)

                # Add user prompt to span attributes
                if current_span and dungeon_request.guidelines:
                    current_span.set_attribute(
                        "user.prompt", dungeon_request.guidelines
                    )
                    current_span.set_attribute(
                        "user.prompt.length", len(dungeon_request.guidelines)
                    )

            except Exception as e:
                return (
                    create_error_response(
                        error="Invalid request parameters",
                        error_type="validation_error",
                        status_code=400,
                        details=str(e),
                        exc_info=sys.exc_info(),
                        additional_context=f"Request validation failed for data: {json.dumps(data, indent=2)}",
                    ).dict(),
                    400,
                )

            # Ensure proper UTF-8 encoding for guidelines text
            try:
                # Validate and normalize UTF-8 encoding
                if isinstance(dungeon_request.guidelines, str):
                    # Ensure the string is properly encoded as UTF-8
                    guidelines_text = dungeon_request.guidelines.encode("utf-8").decode(
                        "utf-8"
                    )
                    # Normalize unicode characters
                    import unicodedata

                    guidelines_text = unicodedata.normalize("NFC", guidelines_text)

                else:
                    guidelines_text = str(dungeon_request.guidelines)
            except UnicodeError as e:
                return (
                    create_error_response(
                        error="Invalid text encoding",
                        error_type="encoding_error",
                        status_code=400,
                        details=f"Text contains invalid characters: {str(e)}",
                        exc_info=sys.exc_info(),
                        additional_context="Text encoding validation failed - ensure input is valid UTF-8",
                    ).dict(),
                    400,
                )

            # Parse user guidelines into structured format
            guidelines = parse_user_guidelines(guidelines_text)

            # Create generation options
            options = GenerationOptions()
            if dungeon_request.options:
                # Apply any custom options to guidelines
                for key, value in dungeon_request.options.items():
                    if hasattr(guidelines, key):
                        setattr(guidelines, key, value)
                    elif hasattr(options, key):
                        setattr(options, key, value)

            # Generate dungeon using the generator
            try:
                result = dungeon_generator.generate_dungeon(guidelines, options)
            except Exception as e:
                print(f"ERROR: Dungeon generation failed with exception: {e}")
                return (
                    create_error_response(
                        error="Generation failed due to an internal error",
                        error_type="generation_error",
                        status_code=500,
                        details=f"Generation failed: {str(e)}",
                        exc_info=sys.exc_info(),
                        additional_context="Exception occurred during dungeon generation process",
                    ).dict(),
                    500,
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
                    return (
                        create_error_response(
                            error="Invalid API Key",
                            error_type="invalid_api_key",
                            status_code=401,
                            details="The GROQ API key is invalid or missing. Please check your API key configuration.",
                            additional_context="API Key validation failed during generation",
                        ).dict(),
                        401,
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
                    return (
                        create_error_response(
                            error="Connection to AI service failed",
                            error_type="connection_error",
                            status_code=503,
                            details="Unable to connect to the AI model service. Please check your connection and try again.",
                            additional_context="Network/connection error during AI service call",
                        ).dict(),
                        503,
                    )
                else:
                    return (
                        create_error_response(
                            error="Generation failed due to an internal error",
                            error_type="generation_error",
                            status_code=500,
                            details="; ".join(result.errors),
                            additional_context="Generation process completed with errors",
                        ).dict(),
                        500,
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

            return response.dict(), 200

        except ValueError as e:
            return (
                create_error_response(
                    error="Invalid request parameters",
                    error_type="validation_error",
                    status_code=400,
                    details=str(e),
                    exc_info=sys.exc_info(),
                    additional_context=f"ValueError occurred while processing request data: {json.dumps(request.get_json() or {}, indent=2)}",
                ).dict(),
                400,
            )
        except Exception as e:
            return (
                create_error_response(
                    error="Unexpected server error",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                    exc_info=sys.exc_info(),
                    additional_context="Unexpected exception in main request handler",
                ).dict(),
                500,
            )

    # Removed _dungeon_to_dict method - now using Pydantic auto-serialization


@generate_ns.route("/info")
class GeneratorInfo(Resource):
    @generate_ns.doc("get_generator_info")
    @generate_ns.response(200, "Success", generator_info_model)
    @generate_ns.response(401, "Unauthorized", error_model)
    @generate_ns.response(500, "Internal Server Error", error_model)
    @simple_trace("get_generator_info")
    @require_auth
    def get(self):
        """Get information about the dungeon generator."""
        try:
            info = dungeon_generator.get_model_info()
            return info, 200
        except Exception as e:
            return (
                create_error_response(
                    error=f"Failed to get info: {str(e)}",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                    exc_info=sys.exc_info(),
                    additional_context="Exception occurred while retrieving generator information",
                ).dict(),
                500,
            )


@generate_bp.route("/info", methods=["GET"])
@simple_trace("get_generator_info")
@require_auth
def get_generator_info_legacy():
    """Get information about the dungeon generator (legacy endpoint)."""
    try:
        info = dungeon_generator.get_model_info()
        return jsonify(info), 200
    except Exception as e:
        return (
            jsonify(
                create_error_response(
                    error=f"Failed to get info: {str(e)}",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                    exc_info=sys.exc_info(),
                    additional_context="Exception occurred while retrieving generator information (legacy endpoint)",
                ).dict()
            ),
            500,
        )
