"""
Utility functions for the DungeonGen backend.
"""

import functools
import os
import sys
import traceback

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

    # Create a JaegerExporter using HTTP endpoint instead of UDP agent
    jaeger_exporter = JaegerExporter(
        collector_endpoint=os.environ.get(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        ),
    )

    # Create a BatchSpanProcessor and add the exporter to the TracerProvider
    processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(processor)

    # Set the TracerProvider as the global default
    trace.set_tracer_provider(provider)

    return trace.get_tracer(__name__)


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
                    # Extract detailed error information
                    location_info = extract_exception_location()
                    full_traceback = traceback.format_exc()

                    # Set error attributes on span
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("error.file", location_info["file"])
                    span.set_attribute("error.line", location_info["line"])
                    span.set_attribute("error.function", location_info["function"])
                    span.set_attribute("response.status", 500)

                    # Log detailed error information
                    print(f"ERROR in {op_name}: {e}")
                    print(
                        f"ERROR Location: {location_info['file']}:{location_info['line']} in {location_info['function']}"
                    )
                    print(f"ERROR Full traceback:\n{full_traceback}")

                    raise

        return wrapper

    return decorator
