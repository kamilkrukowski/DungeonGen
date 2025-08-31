"""
API documentation setup using Flask-RESTX.
"""

from flask_restx import Api, fields


def create_api_docs(app):
    """Create and configure the Flask-RESTX API documentation."""

    api = Api(
        app,
        version="1.0.0",
        title="DungeonGen API",
        description="AI-powered dungeon generation API for creating custom dungeons and adventures",
        doc="/docs",
        authorizations={
            "apikey": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
        },
        security="apikey",
        contact="DungeonGen Team",
        license="MIT",
        license_url="https://opensource.org/licenses/MIT",
    )

    # Define common models for documentation
    error_model = api.model(
        "Error", {"error": fields.String(required=True, description="Error message")}
    )

    health_model = api.model(
        "Health",
        {
            "status": fields.String(required=True, description="Service status"),
            "service": fields.String(required=True, description="Service name"),
        },
    )

    generate_request_model = api.model(
        "GenerateRequest",
        {
            "message": fields.String(
                required=True,
                description="User description of the desired dungeon",
                example="Create a haunted castle with ghostly encounters and hidden passages",
                min_length=1,
                max_length=1000,
            )
        },
    )

    generate_response_model = api.model(
        "GenerateResponse",
        {
            "message": fields.String(
                required=True, description="Generated dungeon description"
            ),
            "user_input": fields.String(
                required=True, description="Original user input"
            ),
            "model": fields.String(
                required=True, description="AI model used for generation"
            ),
            "status": fields.String(required=True, description="Generation status"),
        },
    )

    generator_info_model = api.model(
        "GeneratorInfo",
        {
            "model_name": fields.String(description="Name of the AI model"),
            "model_version": fields.String(description="Version of the model"),
            "capabilities": fields.List(
                fields.String, description="Model capabilities"
            ),
            "max_tokens": fields.Integer(description="Maximum tokens for generation"),
        },
    )

    return api, {
        "error_model": error_model,
        "health_model": health_model,
        "generate_request_model": generate_request_model,
        "generate_response_model": generate_response_model,
        "generator_info_model": generator_info_model,
    }
