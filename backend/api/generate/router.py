"""
Generate endpoint router for dungeon generation.
"""

from flask import Blueprint, jsonify, request
from flask_restx import Namespace, Resource, fields

from src.dungeon.generator import DungeonGenerator
from utils import simple_trace

from .models import ErrorResponse, GenerateRequest, GenerateResponse

# Create blueprint for backward compatibility
generate_bp = Blueprint("generate", __name__, url_prefix="/api/generate")

# Initialize dungeon generator
dungeon_generator = DungeonGenerator()

# Create namespace for Flask-RESTX
generate_ns = Namespace("generate", description="Dungeon generation operations")

# Define models for the namespace
generate_request_model = generate_ns.model(
    "GenerateRequest",
    {
        "message": fields.String(
            required=True,
            description="User description of the desired dungeon",
            example="Create a haunted castle with ghostly encounters and hidden passages",
        )
    },
)

generate_response_model = generate_ns.model(
    "GenerateResponse",
    {
        "message": fields.String(description="Generated dungeon description"),
        "user_input": fields.String(description="Original user input"),
        "model": fields.String(description="AI model used for generation"),
        "status": fields.String(description="Generation status"),
    },
)

error_model = generate_ns.model(
    "Error", {"error": fields.String(description="Error message")}
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


@generate_ns.route("/")
class GenerateDungeon(Resource):
    @generate_ns.doc("generate_dungeon")
    @generate_ns.expect(generate_request_model)
    @generate_ns.response(200, "Success", generate_response_model)
    @generate_ns.response(400, "Bad Request", error_model)
    @generate_ns.response(500, "Internal Server Error", error_model)
    @simple_trace("generate_dungeon")
    def post(self):
        """Generate a dungeon based on user input."""
        try:
            # Validate request data
            data = request.get_json()
            if not data:
                return ErrorResponse(error="No JSON data provided").dict(), 400

            # Validate request using Pydantic model
            try:
                generate_request = GenerateRequest(**data)
            except Exception as e:
                return ErrorResponse(error=f"Invalid request: {str(e)}").dict(), 400

            # Generate dungeon using business logic
            result = dungeon_generator.generate_dungeon(generate_request.message)

            # Validate response using Pydantic model
            response = GenerateResponse(**result)

            return response.dict(), 200

        except ValueError as e:
            return ErrorResponse(error=str(e)).dict(), 400
        except Exception as e:
            return ErrorResponse(error=f"Generation failed: {str(e)}").dict(), 500


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
@generate_bp.route("/", methods=["POST"])
@generate_bp.route("", methods=["POST"])
@simple_trace("generate_dungeon")
def generate_dungeon_legacy():
    """Generate a dungeon based on user input (legacy endpoint)."""
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(error="No JSON data provided").dict()), 400

        # Validate request using Pydantic model
        try:
            generate_request = GenerateRequest(**data)
        except Exception as e:
            return (
                jsonify(ErrorResponse(error=f"Invalid request: {str(e)}").dict()),
                400,
            )

        # Generate dungeon using business logic
        result = dungeon_generator.generate_dungeon(generate_request.message)

        # Validate response using Pydantic model
        response = GenerateResponse(**result)

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
