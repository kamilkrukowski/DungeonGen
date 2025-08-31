"""
Chat endpoint router for conversational dungeon generation.
"""

from flask import Blueprint, jsonify, request
from flask_restx import Namespace, Resource, fields

from src.dungeon.chat_generator import ChatGenerator
from utils import simple_trace

from .models import ChatRequest, ChatResponse, ErrorResponse

# Create blueprint for backward compatibility
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# Initialize chat generator
chat_generator = ChatGenerator()

# Create namespace for Flask-RESTX
chat_ns = Namespace("chat", description="Chat operations")

# Define models for the namespace
chat_request_model = chat_ns.model(
    "ChatRequest",
    {
        "message": fields.String(
            required=True,
            description="User message for chat",
            example="Create a haunted castle with ghostly encounters and hidden passages",
        )
    },
)

chat_response_model = chat_ns.model(
    "ChatResponse",
    {
        "message": fields.String(description="Generated chat response"),
        "user_input": fields.String(description="Original user input"),
        "model": fields.String(description="AI model used for generation"),
        "status": fields.String(description="Generation status"),
    },
)

error_model = chat_ns.model(
    "Error", {"error": fields.String(description="Error message")}
)


@chat_ns.route("/")
class ChatDungeon(Resource):
    @chat_ns.doc("chat_dungeon")
    @chat_ns.expect(chat_request_model)
    @chat_ns.response(200, "Success", chat_response_model)
    @chat_ns.response(400, "Bad Request", error_model)
    @chat_ns.response(500, "Internal Server Error", error_model)
    @simple_trace("chat_dungeon")
    def post(self):
        """Generate a chat response based on user input."""
        try:
            # Validate request data
            data = request.get_json()
            if not data:
                return ErrorResponse(error="No JSON data provided").dict(), 400

            # Validate request using Pydantic model
            try:
                chat_request = ChatRequest(**data)
            except Exception as e:
                return ErrorResponse(error=f"Invalid request: {str(e)}").dict(), 400

            # Generate chat response using business logic
            result = chat_generator.generate_chat_response(chat_request.message)

            # Validate response using Pydantic model
            response = ChatResponse(**result)

            return response.dict(), 200

        except ValueError as e:
            return ErrorResponse(error=str(e)).dict(), 400
        except Exception as e:
            return ErrorResponse(error=f"Chat generation failed: {str(e)}").dict(), 500


# Legacy route handlers for backward compatibility
@chat_bp.route("/", methods=["POST"])
@chat_bp.route("", methods=["POST"])
@simple_trace("chat_dungeon")
def chat_dungeon_legacy():
    """Generate a chat response based on user input (legacy endpoint)."""
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(error="No JSON data provided").dict()), 400

        # Validate request using Pydantic model
        try:
            chat_request = ChatRequest(**data)
        except Exception as e:
            return (
                jsonify(ErrorResponse(error=f"Invalid request: {str(e)}").dict()),
                400,
            )

        # Generate chat response using business logic
        result = chat_generator.generate_chat_response(chat_request.message)

        # Validate response using Pydantic model
        response = ChatResponse(**result)

        return jsonify(response.dict()), 200

    except ValueError as e:
        return jsonify(ErrorResponse(error=str(e)).dict()), 400
    except Exception as e:
        return (
            jsonify(ErrorResponse(error=f"Chat generation failed: {str(e)}").dict()),
            500,
        )
