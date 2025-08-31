"""
Generate endpoint router for structured dungeon generation.
"""

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
                return ErrorResponse(error=f"Invalid request: {str(e)}").dict(), 400

            # Parse user guidelines into structured format
            guidelines = parse_user_guidelines(dungeon_request.guidelines)

            # Create generation options
            options = GenerationOptions()
            if dungeon_request.options:
                # Apply any custom options
                for key, value in dungeon_request.options.items():
                    if hasattr(options, key):
                        setattr(options, key, value)

            # Generate structured dungeon using business logic
            result = dungeon_generator.generate_dungeon(guidelines, options)

            # Convert result to dict format for JSON response
            response_data = {
                "dungeon": self._dungeon_to_dict(result.dungeon),
                "guidelines": {
                    "theme": result.guidelines.theme,
                    "atmosphere": result.guidelines.atmosphere,
                    "difficulty": result.guidelines.difficulty,
                    "room_count": result.guidelines.room_count,
                    "layout_type": result.guidelines.layout_type,
                    "special_requirements": result.guidelines.special_requirements,
                },
                "options": {
                    "include_contents": result.options.include_contents,
                    "include_atmosphere": result.options.include_atmosphere,
                    "include_challenges": result.options.include_challenges,
                    "include_treasures": result.options.include_treasures,
                    "llm_model": result.options.llm_model,
                },
                "generation_time": result.generation_time.isoformat(),
                "status": result.status,
                "errors": result.errors,
            }

            # Validate response using Pydantic model
            response = DungeonGenerateResponse(**response_data)

            return response.dict(), 200

        except ValueError as e:
            return ErrorResponse(error=str(e)).dict(), 400
        except Exception as e:
            return ErrorResponse(error=f"Generation failed: {str(e)}").dict(), 500

    def _dungeon_to_dict(self, dungeon_layout):
        """Convert dungeon layout to dictionary format."""
        return {
            "rooms": [
                {
                    "id": room.id,
                    "name": room.name,
                    "description": room.description,
                    "anchor": (
                        {"x": room.anchor.x, "y": room.anchor.y}
                        if room.anchor
                        else None
                    ),
                    "width": room.width,
                    "height": room.height,
                    "shape": room.shape.value,
                }
                for room in dungeon_layout.rooms
            ],
            "connections": [
                {
                    "room_a_id": conn.room_a_id,
                    "room_b_id": conn.room_b_id,
                    "connection_type": conn.connection_type,
                    "description": conn.description,
                }
                for conn in dungeon_layout.connections
            ],
            "metadata": dungeon_layout.metadata,
        }


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
            return ErrorResponse(error=f"Failed to get info: {str(e)}").dict(), 500


# Legacy route handlers for backward compatibility
@generate_bp.route("/dungeon", methods=["POST"])
@simple_trace("generate_structured_dungeon")
def generate_structured_dungeon_legacy():
    """Generate a structured dungeon based on user guidelines (legacy endpoint)."""
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(error="No JSON data provided").dict()), 400

        # Validate request using Pydantic model
        try:
            dungeon_request = DungeonGenerateRequest(**data)
        except Exception as e:
            return (
                jsonify(ErrorResponse(error=f"Invalid request: {str(e)}").dict()),
                400,
            )

        # Parse user guidelines into structured format
        guidelines = parse_user_guidelines(dungeon_request.guidelines)

        # Create generation options
        options = GenerationOptions()
        if dungeon_request.options:
            # Apply any custom options
            for key, value in dungeon_request.options.items():
                if hasattr(options, key):
                    setattr(options, key, value)

        # Generate structured dungeon using business logic
        result = dungeon_generator.generate_dungeon(guidelines, options)

        # Convert result to dict format for JSON response
        response_data = {
            "dungeon": {
                "rooms": [
                    {
                        "id": room.id,
                        "name": room.name,
                        "description": room.description,
                        "anchor": (
                            {"x": room.anchor.x, "y": room.anchor.y}
                            if room.anchor
                            else None
                        ),
                        "width": room.width,
                        "height": room.height,
                        "shape": room.shape.value,
                    }
                    for room in result.dungeon.rooms
                ],
                "connections": [
                    {
                        "room_a_id": conn.room_a_id,
                        "room_b_id": conn.room_b_id,
                        "connection_type": conn.connection_type,
                        "description": conn.description,
                    }
                    for conn in result.dungeon.connections
                ],
                "metadata": result.dungeon.metadata,
            },
            "guidelines": {
                "theme": result.guidelines.theme,
                "atmosphere": result.guidelines.atmosphere,
                "difficulty": result.guidelines.difficulty,
                "room_count": result.guidelines.room_count,
                "layout_type": result.guidelines.layout_type,
                "special_requirements": result.guidelines.special_requirements,
            },
            "options": {
                "include_contents": result.options.include_contents,
                "include_atmosphere": result.options.include_atmosphere,
                "include_challenges": result.options.include_challenges,
                "include_treasures": result.options.include_treasures,
                "llm_model": result.options.llm_model,
            },
            "generation_time": result.generation_time.isoformat(),
            "status": result.status,
            "errors": result.errors,
        }

        # Validate response using Pydantic model
        response = DungeonGenerateResponse(**response_data)

        return jsonify(response.dict()), 200

    except ValueError as e:
        return jsonify(ErrorResponse(error=str(e)).dict()), 400
    except Exception as e:
        return (
            jsonify(ErrorResponse(error=f"Generation failed: {str(e)}").dict()),
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
            jsonify(ErrorResponse(error=f"Failed to get info: {str(e)}").dict()),
            500,
        )
