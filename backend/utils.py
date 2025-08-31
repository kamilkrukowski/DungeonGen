"""
Utility functions for the DungeonGen backend.
"""

import functools
import os

from flask import request
from opentelemetry import trace


def init_tracer():
    """Initialize OpenTelemetry tracer."""
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Create a resource
    resource = Resource.create({"service.name": "dungeongen-backend"})

    # Create a TracerProvider
    provider = TracerProvider(resource=resource)

    # Create a JaegerExporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.environ.get("JAEGER_AGENT_HOST", "localhost"),
        agent_port=int(os.environ.get("JAEGER_AGENT_PORT", 6831)),
    )

    # Create a BatchSpanProcessor and add the exporter to the TracerProvider
    processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(processor)

    # Set the TracerProvider as the global default
    trace.set_tracer_provider(provider)

    return trace.get_tracer(__name__)


# Initialize tracer
tracer = init_tracer()


def simple_trace(operation_name=None):
    """Simple trace decorator for Flask endpoints."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get operation name from function name if not provided
            op_name = operation_name or func.__name__

            with tracer.start_as_current_span(op_name) as span:
                # Add request info to span
                if hasattr(request, "method"):
                    span.set_attribute("http.method", request.method)
                if hasattr(request, "url"):
                    span.set_attribute("http.url", request.url)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("response.status", 200)
                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("response.status", 500)
                    raise

        return wrapper

    return decorator
