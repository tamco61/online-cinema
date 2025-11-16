"""
Security utilities for authentication and authorization.

This module provides:
- Password hashing and verification using bcrypt
- Authentication dependencies for protecting endpoints
"""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.jwt_service import get_jwt_service

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme for extracting JWT tokens from headers
security = HTTPBearer()


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

        if verify_password(password, user.password_hash):
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

        hashed = get_password_hash("MyPassword123")
        ```
    """
    return pwd_context.hash(password)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    """
    Dependency to get current user ID from JWT token.

    Extracts and validates JWT access token from Authorization header.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid or expired

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.core.security import get_current_user_id

        router = APIRouter()

        @router.get("/profile")
        async def get_profile(user_id: uuid.UUID = Depends(get_current_user_id)):
            return {"user_id": str(user_id)}
        ```
    """
    jwt_service = get_jwt_service()

    # Extract token from credentials
    token = credentials.credentials

    # Verify and decode token
    user_id = jwt_service.verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Dependency to get current user from database.

    Retrieves full user object based on authenticated user ID.

    Args:
        user_id: User ID from JWT token
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If user not found or inactive

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.core.security import get_current_user
        from app.db.models import User

        router = APIRouter()

        @router.get("/me")
        async def read_current_user(user: User = Depends(get_current_user)):
            return {"email": user.email}
        ```
    """
    from app.db.models import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[uuid.UUID]:
    """
    Optional dependency to get current user ID.

    Returns None if no token is provided instead of raising an error.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        User ID if valid token provided, None otherwise

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.core.security import get_optional_current_user_id

        router = APIRouter()

        @router.get("/public-or-private")
        async def mixed_endpoint(user_id: Optional[uuid.UUID] = Depends(get_optional_current_user_id)):
            if user_id:
                return {"message": "Authenticated", "user_id": str(user_id)}
            return {"message": "Anonymous"}
        ```
    """
    if credentials is None:
        return None

    jwt_service = get_jwt_service()
    token = credentials.credentials

    return jwt_service.verify_access_token(token)
