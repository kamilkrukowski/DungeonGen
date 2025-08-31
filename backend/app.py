import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_restx import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Import API documentation
from api.docs import create_api_docs

# Register API blueprints
from api.generate.router import generate_bp, generate_ns

# Import utilities
from utils import simple_trace

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(
    app,
    origins=["http://localhost:3000", "http://frontend:3000"],
    supports_credentials=False,
)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Create API documentation
api, models = create_api_docs(app)

# Register blueprints
app.register_blueprint(generate_bp)

# Register namespaces
api.add_namespace(generate_ns, path="/api/generate")

# Create namespaces for better organization
health_ns = api.namespace("health", description="Health check operations")


@health_ns.route("/")
class HealthCheck(Resource):
    @api.doc("health_check")
    @api.response(200, "Success", models["health_model"])
    @simple_trace("health_check_endpoint")
    def get(self):
        """Check the health status of the API."""
        result = {"status": "healthy", "service": "dungeongen-backend"}
        return result


@api.route("/")
class Home(Resource):
    @api.doc("home")
    def get(self):
        """Get API information and available endpoints."""
        result = {
            "message": "DungeonGen Backend API",
            "status": "running",
            "version": "1.0.0",
            "endpoints": {
                "generate": "/api/generate",
                "generate_info": "/api/generate/info",
                "health": "/api/health",
                "docs": "/docs",
            },
        }
        return result


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
