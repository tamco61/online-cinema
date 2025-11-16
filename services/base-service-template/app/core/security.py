"""
Security utilities for authentication and authorization.

This module provides:
- JWT token generation and validation
- Password hashing and verification
- Authentication dependencies
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create JWT access token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Token expiration time (default: from settings)
        additional_claims: Additional claims to include in token

    Returns:
        Encoded JWT token

    Example:
        ```python
        from app.core.security import create_access_token

        token = create_access_token(subject=user_id)
        ```
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }

    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Token expiration time (default: from settings)

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired

    Example:
        ```python
        from app.core.security import decode_token

        try:
            payload = decode_token(token)
            user_id = payload["sub"]
        except JWTError:
            # Handle invalid token
            pass
        ```
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise

    Example:
        ```python
        from app.core.security import verify_password

        if verify_password(password, user.hashed_password):
            # Password is correct
            pass
        ```
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password

    Example:
        ```python
        from app.core.security import get_password_hash

        hashed = get_password_hash("secret123")
        ```
    """
    return pwd_context.hash(password)
