"""
FastAPI authentication router for login and JWT token management.
"""

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import LoginRequest, LoginResponse
from .utils import (
    authenticate_admin,
    create_jwt_token,
    get_admin_password_hash,
    verify_jwt_token,
)

# Create router
auth_router = APIRouter()

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Dependency to get current authenticated user."""
    token = credentials.credentials

    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate admin user and return JWT token."""
    try:
        # Check if admin password hash is configured
        admin_hash = get_admin_password_hash()
        if not admin_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured - ADMIN_PASSWORD_HASH environment variable not set",
            )

        # Authenticate user
        if not authenticate_admin(request.password):
            # Add delay for failed login attempts to prevent brute force attacks
            time.sleep(0.1)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
            )

        # Create JWT token
        try:
            token = create_jwt_token("admin")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token creation failed: {str(e)}",
            )

        # Return success response
        return LoginResponse(token=token, message="Login successful")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {str(e)}",
        )


@auth_router.get("/verify")
async def verify_token(current_user: dict[str, Any] = Depends(get_current_user)):
    """Verify if the current JWT token is valid."""
    return {
        "valid": True,
        "user_id": current_user.get("user_id"),
        "expires_at": current_user.get("exp"),
    }
