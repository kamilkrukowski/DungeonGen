"""
AWS Lambda handler for DungeonGen Flask application.
This module provides the entry point for AWS Lambda using the Lambda Web Adapter.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import the Lambda-optimized Flask app
from app_lambda import app


# Lambda Web Adapter handler
def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    This function is called by AWS Lambda and uses the Lambda Web Adapter
    to convert the Lambda event into a WSGI request for Flask.

    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object

    Returns:
        dict: Response object with statusCode, headers, and body
    """
    from mangum import Mangum

    # Create Mangum adapter for Flask
    handler = Mangum(app, lifespan="off")

    # Process the request
    response = handler(event, context)

    return response
