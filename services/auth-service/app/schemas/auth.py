"""
Pydantic schemas for authentication endpoints.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password complexity.

        Password must contain:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenPair(BaseModel):
    """Schema for JWT token pair."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """Schema for new access token response."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class UserResponse(BaseModel):
    """Schema for user info response."""

    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation date")

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Schema for authentication response (login/register)."""

    user: UserResponse = Field(..., description="User information")
    tokens: TokenPair = Field(..., description="Authentication tokens")


class LogoutRequest(BaseModel):
    """Schema for logout request."""

    refresh_token: str = Field(..., description="Refresh token to invalidate")


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(..., description="Response message")


# OAuth Schemas (stubs for future implementation)


class OAuthAuthorizationRequest(BaseModel):
    """Schema for OAuth authorization initiation."""

    redirect_uri: Optional[str] = Field(
        None,
        description="Redirect URI after OAuth flow",
    )


class OAuthAuthorizationResponse(BaseModel):
    """Schema for OAuth authorization response."""

    authorization_url: str = Field(..., description="OAuth provider authorization URL")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback."""

    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="OAuth state parameter")


class OAuthCallbackResponse(BaseModel):
    """Schema for OAuth callback response."""

    user: UserResponse = Field(..., description="User information")
    tokens: TokenPair = Field(..., description="Authentication tokens")
    is_new_user: bool = Field(..., description="Whether this is a newly created user")
