"""
Generate endpoint router for dungeon generation.
"""

from flask import Blueprint, jsonify, request

from src.dungeon.generator import DungeonGenerator

from .models import ErrorResponse, GenerateRequest, GenerateResponse

# Create blueprint
generate_bp = Blueprint("generate", __name__, url_prefix="/api/generate")

# Initialize dungeon generator
dungeon_generator = DungeonGenerator()


@generate_bp.route("/", methods=["POST"])
@generate_bp.route("", methods=["POST"])
def generate_dungeon():
    """Generate a dungeon based on user input."""
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
def get_generator_info():
    """Get information about the dungeon generator."""
    try:
        info = dungeon_generator.get_model_info()
        return jsonify(info), 200
    except Exception as e:
        return (
            jsonify(ErrorResponse(error=f"Failed to get info: {str(e)}").dict()),
            500,
        )
