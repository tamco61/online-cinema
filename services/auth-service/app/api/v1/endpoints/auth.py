"""
Authentication endpoints.

Handles user registration, login, token refresh, and logout.
"""

import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_auth_service_dep
from app.core.security import get_current_user, get_current_user_id
from app.db.models import User
from app.schemas.auth import (
    AuthResponse,
    LogoutRequest,
    MessageResponse,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()

# In-memory rate limiting (simple implementation)
# Format: {ip_address: {endpoint: [timestamp1, timestamp2, ...]}}
rate_limit_storage: Dict[str, Dict[str, list]] = {}


def check_rate_limit(request: Request, endpoint: str, max_per_minute: int = 5) -> None:
    """
    Simple in-memory rate limiting.

    Args:
        request: FastAPI request object
        endpoint: Endpoint identifier
        max_per_minute: Maximum requests per minute

    Raises:
        HTTPException: If rate limit exceeded
    """
    import time

    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    cleanup_time = current_time - 60  # 60 seconds ago

    # Initialize storage for this IP if needed
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = {}

    if endpoint not in rate_limit_storage[client_ip]:
        rate_limit_storage[client_ip][endpoint] = []

    # Clean up old timestamps
    rate_limit_storage[client_ip][endpoint] = [
        ts for ts in rate_limit_storage[client_ip][endpoint]
        if ts > cleanup_time
    ]

    # Check rate limit
    if len(rate_limit_storage[client_ip][endpoint]) >= max_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {max_per_minute} requests per minute.",
        )

    # Add current request timestamp
    rate_limit_storage[client_ip][endpoint].append(current_time)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password",
)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service_dep),
) -> AuthResponse:
    """
    Register a new user.

    - **email**: Valid email address
    - **password**: Password (min 8 chars, must contain uppercase, lowercase, and digit)

    Returns user info and authentication tokens.
    """
    return await auth_service.register(
        email=user_data.email,
        password=user_data.password,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Authenticate user and receive access and refresh tokens",
)
async def login(
    request: Request,
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service_dep),
) -> AuthResponse:
    """
    Authenticate user and issue tokens.

    Rate limited to 5 attempts per minute per IP address.

    - **email**: User email
    - **password**: User password

    Returns user info and authentication tokens.
    """
    # Apply rate limiting
    check_rate_limit(request, "login", max_per_minute=5)

    return await auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token",
)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service_dep),
) -> TokenResponse:
    """
    Refresh access token.

    - **refresh_token**: Valid refresh token

    Returns a new access token.
    """
    return await auth_service.refresh_access_token(
        refresh_token=token_data.refresh_token,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate refresh token (logout from current device)",
)
async def logout(
    logout_data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service_dep),
) -> MessageResponse:
    """
    Logout user by invalidating refresh token.

    - **refresh_token**: Refresh token to invalidate

    Returns success message.
    """
    success = await auth_service.logout(
        refresh_token=logout_data.refresh_token,
    )

    if success:
        return MessageResponse(message="Successfully logged out")
    else:
        return MessageResponse(message="Token not found or already invalidated")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout from all devices",
    description="Invalidate all refresh tokens for the authenticated user",
    dependencies=[Depends(get_current_user_id)],
)
async def logout_all(
    user_id: uuid.UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service_dep),
) -> MessageResponse:
    """
    Logout user from all devices.

    Requires authentication (access token in Authorization header).

    Returns number of sessions invalidated.
    """
    count = await auth_service.logout_all_sessions(user_id)

    return MessageResponse(
        message=f"Successfully logged out from {count} device(s)"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Get information about the authenticated user",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Requires authentication (access token in Authorization header).

    Returns user information.
    """
    return UserResponse.model_validate(current_user)
