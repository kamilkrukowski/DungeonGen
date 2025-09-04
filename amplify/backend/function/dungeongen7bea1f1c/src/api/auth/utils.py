"""
Authentication utilities for JWT token handling and password verification.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import jwt

try:
    from flask import jsonify, request

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    jsonify = None
    request = None

# JWT Configuration
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "your-secret-key-change-in-production"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.

    Args:
        password: Plain text password

    Returns:
        Hashed password string with salt
    """
    # Generate a random salt
    salt = secrets.token_hex(16)

    # Hash the password with the salt using PBKDF2
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )

    # Return salt and hash combined
    return f"{salt}:{password_hash.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        hashed_password: Hashed password to verify against (format: salt:hash)

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        salt, stored_hash = hashed_password.split(":", 1)

        # Hash the provided password with the stored salt
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )

        # Compare hashes
        return password_hash.hex() == stored_hash
    except Exception:
        return False


def create_jwt_token(user_id: str = "admin") -> str:
    """
    Create a JWT token for the given user.

    Args:
        user_id: User identifier (defaults to "admin")

    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
        "iss": "dungeongen-api",
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_admin_password_hash() -> str | None:
    """
    Get the admin password hash from environment variables.

    Returns:
        Admin password hash or None if not set
    """
    return os.environ.get("ADMIN_PASSWORD_HASH")


def authenticate_admin(password: str) -> bool:
    """
    Authenticate admin user by comparing password with stored hash.

    Args:
        password: Plain text password

    Returns:
        True if authentication successful, False otherwise
    """
    admin_hash = get_admin_password_hash()
    if not admin_hash:
        # If no hash is set, deny access
        return False

    return verify_password(password, admin_hash)


def require_auth(f):
    """
    Decorator to require JWT authentication for endpoints.

    Args:
        f: Function to decorate

    Returns:
        Decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only work if Flask is available
        if not FLASK_AVAILABLE or request is None:
            return f(*args, **kwargs)

        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            if jsonify is not None:
                return (
                    jsonify(
                        {
                            "error": "Authorization header missing",
                            "error_type": "authentication_error",
                            "status_code": 401,
                        }
                    ),
                    401,
                )
            else:
                return {"error": "Authorization header missing"}, 401

        # Check if header starts with "Bearer "
        if not auth_header.startswith("Bearer "):
            if jsonify is not None:
                return (
                    jsonify(
                        {
                            "error": "Invalid authorization header format",
                            "error_type": "authentication_error",
                            "status_code": 401,
                        }
                    ),
                    401,
                )
            else:
                return {"error": "Invalid authorization header format"}, 401

        # Extract token
        token = auth_header.split(" ")[1]

        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            if jsonify is not None:
                return (
                    jsonify(
                        {
                            "error": "Invalid or expired token",
                            "error_type": "authentication_error",
                            "status_code": 401,
                        }
                    ),
                    401,
                )
            else:
                return {"error": "Invalid or expired token"}, 401

        # Add user info to request context (only if Flask is available)
        if FLASK_AVAILABLE and request is not None:
            request.user_id = payload.get("user_id")
            request.user_payload = payload

        return f(*args, **kwargs)

    return decorated_function
