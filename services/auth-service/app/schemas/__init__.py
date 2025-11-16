"""
Pydantic schemas for Auth Service.
"""

from .auth import (
    AuthResponse,
    LogoutRequest,
    MessageResponse,
    OAuthAuthorizationRequest,
    OAuthAuthorizationResponse,
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    TokenPair,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "TokenPair",
    "TokenRefresh",
    "TokenResponse",
    "UserResponse",
    "AuthResponse",
    "LogoutRequest",
    "MessageResponse",
    "OAuthAuthorizationRequest",
    "OAuthAuthorizationResponse",
    "OAuthCallbackRequest",
    "OAuthCallbackResponse",
]
