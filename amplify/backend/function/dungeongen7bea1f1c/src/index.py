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
