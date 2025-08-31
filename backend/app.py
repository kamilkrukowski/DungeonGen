import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Register API blueprints
from api.generate.router import generate_bp

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

app.register_blueprint(generate_bp)


@app.route("/")
@simple_trace("home_endpoint")
def home():
    result = {
        "message": "DungeonGen Backend API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "generate_info": "/api/generate/info",
            "health": "/api/health",
        },
    }
    return jsonify(result)


@app.route("/api/health")
@simple_trace("health_check_endpoint")
def health_check():
    result = {"status": "healthy", "service": "dungeongen-backend"}
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
