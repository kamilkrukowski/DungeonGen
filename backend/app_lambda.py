"""
Lambda-optimized Flask application for DungeonGen.
This version is optimized for AWS Lambda deployment with minimal cold start impact.
"""

import os
import sys
import traceback
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Resource

# Import API documentation
from api.docs import create_api_docs

# Register API blueprints
from api.auth.router import auth_bp, auth_ns
from api.generate.router import generate_bp, generate_ns

# Import utilities
from utils import simple_trace

# Load environment variables
load_dotenv()

# Check GROQ API key availability
groq_api_key = os.environ.get("GROQ_API_KEY")
if groq_api_key:
    # Strip newlines and whitespace from API key to prevent httpx header errors
    groq_api_key = groq_api_key.strip()

    if len(groq_api_key) > 6:
        masked_key = groq_api_key[:3] + "***" + groq_api_key[-3:]
    else:
        masked_key = "***" + groq_api_key[-3:] if len(groq_api_key) > 3 else "***"
else:
    pass


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


# Create Flask app with Lambda optimizations
app = Flask(__name__)

# Configure Flask for Lambda
app.config["JSON_AS_ASCII"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# CORS configuration for Lambda
# In Lambda, we need to handle CORS more dynamically
CORS(
    app,
    origins=["*"],  # Lambda will handle CORS at API Gateway level
    supports_credentials=False,
)

# Skip OpenTelemetry instrumentation in Lambda for better performance
# FlaskInstrumentor().instrument_app(app)  # Commented out for Lambda

# Create API documentation
api, models = create_api_docs(app)

# Register blueprints
app.register_blueprint(generate_bp)
app.register_blueprint(auth_bp)

# Register namespaces
api.add_namespace(generate_ns, path="/api/generate")
api.add_namespace(auth_ns, path="/api/auth")

# Create namespaces for better organization
health_ns = api.namespace("health", description="Health check operations")


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Global error handler for unexpected exceptions."""
    # Extract location information
    location_info = extract_exception_location()

    # Get full traceback
    full_traceback = traceback.format_exc()

    # Build location string, handling None values gracefully
    location_str = f"File: {location_info['file']}"
    if location_info["line"] is not None:
        location_str += f"\nLine: {location_info['line']}"
    else:
        location_str += "\nLine: unknown"
    location_str += f"\nFunction: {location_info['function']}"

    # Build enhanced error response
    error_response = {
        "error": "Unexpected server error",
        "error_type": "internal_error",
        "status_code": 500,
        "details": str(error),
        "traceback": f"""Error Location:
{location_str}

Unexpected exception in global error handler

Full Traceback:
{full_traceback}""",
        "location": {
            "file": location_info["file"],
            "line": location_info["line"],
            "function": location_info["function"],
        },
    }

    # Log the error for debugging (CloudWatch in Lambda)
    print(f"ERROR: Unexpected exception: {error}")
    print(
        f"ERROR Location: {location_info['file']}:{location_info['line']} in {location_info['function']}"
    )
    print(f"ERROR Full traceback:\n{full_traceback}")

    return jsonify(error_response), 500


@health_ns.route("/")
class HealthCheck(Resource):
    @api.doc("health_check")
    @api.response(200, "Success", models["health_model"])
    @simple_trace("health_check_endpoint")
    def get(self):
        """Check the health status of the API."""
        result = {
            "status": "healthy", 
            "service": "dungeongen-backend-lambda",
            "runtime": "aws-lambda"
        }
        return result


@api.route("/")
class Home(Resource):
    @api.doc("home")
    def get(self):
        """Get API information and available endpoints."""
        result = {
            "message": "DungeonGen Backend API (Lambda)",
            "status": "running",
            "version": "1.0.0",
            "runtime": "aws-lambda",
            "endpoints": {
                "auth": "/api/auth/login",
                "generate": "/api/generate/dungeon",
                "generate_info": "/api/generate/info",
                "health": "/api/health",
                "docs": "/docs",
            },
        }
        return result


# Lambda-specific initialization
def init_lambda():
    """Initialize Lambda-specific configurations."""
    # Set environment variables for Lambda
    os.environ.setdefault("FLASK_ENV", "production")
    
    # Disable debug mode in Lambda
    app.config["DEBUG"] = False
    
    # Optimize for Lambda cold starts
    print("Lambda initialization complete")


# Initialize when module is imported
init_lambda()
