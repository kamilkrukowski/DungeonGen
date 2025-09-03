"""
Generate endpoint router for structured dungeon generation.
"""

import json
import traceback

from flask import Blueprint, jsonify, request
from flask_restx import Namespace, Resource, fields

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


@generate_ns.route("/dungeon")
class GenerateStructuredDungeon(Resource):
    @generate_ns.doc("generate_structured_dungeon")
    @generate_ns.expect(dungeon_generate_request_model)
    @generate_ns.response(200, "Success", dungeon_generate_response_model)
    @generate_ns.response(400, "Bad Request", error_model)
    @generate_ns.response(500, "Internal Server Error", error_model)
    @simple_trace("generate_structured_dungeon")
    def post(self):
        """Generate a structured dungeon based on user guidelines."""
        try:
            # Validate request data
            data = request.get_json()
            if not data:
                return ErrorResponse(error="No JSON data provided").dict(), 400

            # Validate request using Pydantic model
            try:
                dungeon_request = DungeonGenerateRequest(**data)
            except Exception as e:
                return (
                    ErrorResponse(
                        error="Invalid request parameters",
                        error_type="validation_error",
                        status_code=400,
                        details=str(e),
                        traceback=f"Request Validation Error:\n{str(e)}\n\nRequest Data:\n{json.dumps(data, indent=2)}",
                    ).dict(),
                    400,
                )

            # Parse user guidelines into structured format
            guidelines = parse_user_guidelines(dungeon_request.guidelines)
            print(
                f"DEBUG: Initial guidelines: room_count={guidelines.room_count}, layout_type={guidelines.layout_type}",
                flush=True,
            )

            # Create generation options
            options = GenerationOptions()
            if dungeon_request.options:
                print(f"DEBUG: Applying options: {dungeon_request.options}", flush=True)
                # Apply any custom options to guidelines
                for key, value in dungeon_request.options.items():
                    if hasattr(guidelines, key):
                        print(f"DEBUG: Setting guidelines.{key} = {value}", flush=True)
                        setattr(guidelines, key, value)
                    elif hasattr(options, key):
                        print(f"DEBUG: Setting options.{key} = {value}", flush=True)
                        setattr(options, key, value)

            print(
                f"DEBUG: Final guidelines: room_count={guidelines.room_count}, layout_type={guidelines.layout_type}",
                flush=True,
            )

            # Generate dungeon using the generator
            result = dungeon_generator.generate_dungeon(guidelines, options)

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
                        ErrorResponse(
                            error="Invalid API Key",
                            error_type="invalid_api_key",
                            status_code=401,
                            details="The GROQ API key is invalid or missing. Please check your API key configuration.",
                            traceback="API Key Error Details:\n"
                            + "\n".join(result.errors),
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
                        ErrorResponse(
                            error="Connection to AI service failed",
                            error_type="connection_error",
                            status_code=503,
                            details="Unable to connect to the AI model service. Please check your connection and try again.",
                            traceback="Connection Error Details:\n"
                            + "\n".join(result.errors),
                        ).dict(),
                        503,
                    )
                else:
                    return (
                        ErrorResponse(
                            error="Generation failed due to an internal error",
                            error_type="generation_error",
                            status_code=500,
                            details="; ".join(result.errors),
                            traceback="Generation Errors:\n" + "\n".join(result.errors),
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
                ErrorResponse(
                    error="Invalid request parameters",
                    error_type="validation_error",
                    status_code=400,
                    details=str(e),
                    traceback=f"ValueError Details:\n{str(e)}\n\nRequest Data:\n{json.dumps(request.get_json() or {}, indent=2)}",
                ).dict(),
                400,
            )
        except Exception as e:
            return (
                ErrorResponse(
                    error="Unexpected server error",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                    traceback=traceback.format_exc(),
                ).dict(),
                500,
            )

    # Removed _dungeon_to_dict method - now using Pydantic auto-serialization


@generate_ns.route("/info")
class GeneratorInfo(Resource):
    @generate_ns.doc("get_generator_info")
    @generate_ns.response(200, "Success", generator_info_model)
    @generate_ns.response(500, "Internal Server Error", error_model)
    @simple_trace("get_generator_info")
    def get(self):
        """Get information about the dungeon generator."""
        try:
            info = dungeon_generator.get_model_info()
            return info, 200
        except Exception as e:
            return (
                ErrorResponse(
                    error=f"Failed to get info: {str(e)}",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                    traceback=traceback.format_exc(),
                ).dict(),
                500,
            )


@generate_bp.route("/info", methods=["GET"])
@simple_trace("get_generator_info")
def get_generator_info_legacy():
    """Get information about the dungeon generator (legacy endpoint)."""
    try:
        info = dungeon_generator.get_model_info()
        return jsonify(info), 200
    except Exception as e:
        return (
            jsonify(
                ErrorResponse(
                    error=f"Failed to get info: {str(e)}",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                    traceback=traceback.format_exc(),
                ).dict()
            ),
            500,
        )
