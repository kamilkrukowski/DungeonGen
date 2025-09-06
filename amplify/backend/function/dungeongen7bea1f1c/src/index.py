"""
AWS Lambda handler for DungeonGen FastAPI application using Mangum.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Import the FastAPI app
from mangum import Mangum  # NOQA: E402

try:
    # Debug: Check numpy availability with detailed diagnostics
    import os
    import sys

    print(f"Python version: {sys.version}", flush=True)
    print(f"Python path: {sys.path}", flush=True)
    print(f"Current working directory: {os.getcwd()}", flush=True)
    print(f"Files in current directory: {os.listdir('.')}", flush=True)

    # Check if numpy files exist
    try:
        import site

        site_packages = site.getsitepackages()
        print(f"Site packages directories: {site_packages}", flush=True)

        for site_dir in site_packages:
            numpy_path = os.path.join(site_dir, "numpy")
            if os.path.exists(numpy_path):
                print(f"NumPy found at: {numpy_path}", flush=True)
                print(f"NumPy contents: {os.listdir(numpy_path)}", flush=True)
            else:
                print(f"NumPy not found at: {numpy_path}", flush=True)
    except Exception as e:
        print(f"Error checking site packages: {e}", flush=True)

    # Try importing numpy with detailed error info
    try:
        import numpy

        print(f"NumPy successfully imported: {numpy.__version__}", flush=True)
        print(f"NumPy location: {numpy.__file__}", flush=True)
        print(f"NumPy array test: {numpy.array([1, 2, 3])}", flush=True)
    except ImportError as e:
        print(f"NumPy import failed: {e}", flush=True)
        print(f"Import error type: {type(e)}", flush=True)
        import traceback

        traceback.print_exc()
    except Exception as e:
        print(f"NumPy other error: {e}", flush=True)
        import traceback

        traceback.print_exc()

    from fastapi_app import app  # NOQA: E402

    print("FastAPI app imported successfully", flush=True)
except Exception as e:
    print(f"Error importing FastAPI app: {e}", flush=True)
    import traceback

    traceback.print_exc()
    raise

# Create Mangum adapter for FastAPI
mangum_handler = Mangum(app, lifespan="off")


# Create debug wrapper to see what API Gateway is sending
def handler(event, context):
    print(f"Lambda event: {event}", flush=True)
    print(f"Lambda context: {context}", flush=True)

    # Fix the path for API Gateway proxy integration
    if "path" in event and event["path"].startswith("/stuff/"):
        # Remove /stuff prefix from the path
        original_path = event["path"]
        event["path"] = event["path"][6:]  # Remove '/stuff'
        print(f"Modified path from {original_path} to {event['path']}", flush=True)

    return mangum_handler(event, context)


print("Mangum handler created successfully")
