import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_opentracing import FlaskTracing
from jaeger_client import Config

# Register API blueprints
from api.generate import generate_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False)


# Initialize Jaeger tracer
def init_tracer():
    config = Config(
        config={
            "sampler": {
                "type": "const",
                "param": 1,
            },
            "local_agent": {
                "reporting_host": os.environ.get("JAEGER_AGENT_HOST", "localhost"),
                "reporting_port": int(os.environ.get("JAEGER_AGENT_PORT", 6831)),
            },
            "logging": True,
        },
        service_name=os.environ.get("JAEGER_SERVICE_NAME", "dungeongen-backend"),
        validate=True,
    )
    return config.initialize_tracer()


# Initialize tracer
tracer = init_tracer()
tracing = FlaskTracing(tracer, True, app)


app.register_blueprint(generate_bp)


@app.route("/")
def home():
    with tracer.start_span("home_endpoint") as span:
        span.set_tag("endpoint", "/")
        span.set_tag("method", "GET")

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

        span.set_tag("response.status", 200)
        return jsonify(result)


@app.route("/api/health")
def health_check():
    with tracer.start_span("health_check_endpoint") as span:
        span.set_tag("endpoint", "/api/health")
        span.set_tag("method", "GET")

        result = {"status": "healthy", "service": "dungeongen-backend"}

        span.set_tag("response.status", 200)
        return jsonify(result)


@app.route("/api/trace-test")
def trace_test():
    with tracer.start_span("trace_test_endpoint") as span:
        span.set_tag("endpoint", "/api/trace-test")
        span.set_tag("method", "GET")

        # Simulate some work
        with tracer.start_span("simulate_work") as work_span:
            work_span.set_tag("work.type", "simulation")
            import time

            time.sleep(0.1)  # Simulate some processing time

        result = {
            "message": "Trace test endpoint",
            "tracing_enabled": True,
            "service": "dungeongen-backend",
        }

        span.set_tag("response.status", 200)
        return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
