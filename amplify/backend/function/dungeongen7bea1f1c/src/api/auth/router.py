"""
Authentication router for login and JWT token management.
"""

import time

from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields

from utils import simple_trace

from .models import AuthErrorResponse, LoginRequest, LoginResponse
from .utils import authenticate_admin, create_jwt_token, get_admin_password_hash

# Create blueprint for backward compatibility
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Create namespace for Flask-RESTX
auth_ns = Namespace("auth", description="Authentication operations")

# Define models for API documentation
login_request_model = auth_ns.model(
    "LoginRequest",
    {
        "password": fields.String(
            required=True, description="Admin password", example="your-admin-password"
        ),
    },
)

login_response_model = auth_ns.model(
    "LoginResponse",
    {
        "token": fields.String(description="JWT access token"),
        "message": fields.String(description="Success message"),
    },
)

auth_error_model = auth_ns.model(
    "AuthError",
    {
        "error": fields.String(description="Error message"),
        "error_type": fields.String(description="Error type"),
        "status_code": fields.Integer(description="HTTP status code"),
    },
)


def create_auth_error_response(
    error: str,
    error_type: str = "authentication_error",
    status_code: int = 401,
    details: str = "",
) -> AuthErrorResponse:
    """
    Create an authentication error response.

    Args:
        error: Main error message
        error_type: Type of error
        status_code: HTTP status code
        details: Additional error details

    Returns:
        AuthErrorResponse object
    """
    return AuthErrorResponse(
        error=error,
        error_type=error_type,
        status_code=status_code,
    )


@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.doc("login")
    @auth_ns.expect(login_request_model)
    @auth_ns.response(200, "Success", login_response_model)
    @auth_ns.response(400, "Bad Request", auth_error_model)
    @auth_ns.response(401, "Unauthorized", auth_error_model)
    @auth_ns.response(500, "Internal Server Error", auth_error_model)
    @simple_trace("login")
    def post(self):
        """Authenticate admin user and return JWT token."""
        try:
            # Check if admin password hash is configured
            admin_hash = get_admin_password_hash()
            if not admin_hash:
                return (
                    create_auth_error_response(
                        error="Authentication not configured",
                        error_type="configuration_error",
                        status_code=500,
                        details="ADMIN_PASSWORD_HASH environment variable not set",
                    ).dict(),
                    500,
                )

            # Validate request data
            data = request.get_json()
            if not data:
                return (
                    create_auth_error_response(
                        error="No JSON data provided",
                        error_type="validation_error",
                        status_code=400,
                        details="Request body is empty or not valid JSON",
                    ).dict(),
                    400,
                )

            # Validate request using Pydantic model
            try:
                login_request = LoginRequest(**data)
            except Exception as e:
                return (
                    create_auth_error_response(
                        error="Invalid request parameters",
                        error_type="validation_error",
                        status_code=400,
                        details=str(e),
                    ).dict(),
                    400,
                )

            # Authenticate user
            if not authenticate_admin(login_request.password):
                # Add delay for failed login attempts to prevent brute force attacks
                time.sleep(0.1)
                return (
                    create_auth_error_response(
                        error="Invalid password",
                        error_type="authentication_error",
                        status_code=401,
                        details="The provided password is incorrect",
                    ).dict(),
                    401,
                )

            # Create JWT token
            try:
                token = create_jwt_token("admin")
            except Exception as e:
                return (
                    create_auth_error_response(
                        error="Token creation failed",
                        error_type="internal_error",
                        status_code=500,
                        details=f"Failed to create JWT token: {str(e)}",
                    ).dict(),
                    500,
                )

            # Return success response
            response = LoginResponse(token=token, message="Login successful")
            return response.dict(), 200

        except Exception as e:
            return (
                create_auth_error_response(
                    error="Unexpected server error",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                ).dict(),
                500,
            )


@auth_ns.route("/verify")
class VerifyToken(Resource):
    @auth_ns.doc("verify_token")
    @auth_ns.response(200, "Success")
    @auth_ns.response(401, "Unauthorized", auth_error_model)
    @simple_trace("verify_token")
    def get(self):
        """Verify if the current JWT token is valid."""
        try:
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return (
                    create_auth_error_response(
                        error="Authorization header missing",
                        error_type="authentication_error",
                        status_code=401,
                    ).dict(),
                    401,
                )

            # Check if header starts with "Bearer "
            if not auth_header.startswith("Bearer "):
                return (
                    create_auth_error_response(
                        error="Invalid authorization header format",
                        error_type="authentication_error",
                        status_code=401,
                    ).dict(),
                    401,
                )

            # Extract and verify token
            token = auth_header.split(" ")[1]
            from .utils import verify_jwt_token

            payload = verify_jwt_token(token)
            if not payload:
                return (
                    create_auth_error_response(
                        error="Invalid or expired token",
                        error_type="authentication_error",
                        status_code=401,
                    ).dict(),
                    401,
                )

            # Return success response
            return {
                "valid": True,
                "user_id": payload.get("user_id"),
                "expires_at": payload.get("exp"),
            }, 200

        except Exception as e:
            return (
                create_auth_error_response(
                    error="Token verification failed",
                    error_type="internal_error",
                    status_code=500,
                    details=str(e),
                ).dict(),
                500,
            )
