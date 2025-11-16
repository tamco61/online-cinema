"""
FastAPI dependencies.

Common dependencies used across API endpoints.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
) -> int:
    """
    Dependency to get current user ID from JWT token.

    Args:
        authorization: Authorization header (Bearer token)

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid or missing

    Example:
        ```python
        from fastapi import Depends
        from app.api.deps import get_current_user_id

        @app.get("/profile")
        async def get_profile(user_id: int = Depends(get_current_user_id)):
            return {"user_id": user_id}
        ```
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate token
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return user_id

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_optional_current_user_id(
    authorization: Optional[str] = Header(None),
) -> Optional[int]:
    """
    Dependency to get current user ID (optional).

    Returns None if no token is provided.

    Args:
        authorization: Authorization header (Bearer token)

    Returns:
        User ID or None
    """
    if not authorization:
        return None

    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None


# Alias for convenience
CurrentUser = Depends(get_current_user_id)
OptionalCurrentUser = Depends(get_optional_current_user_id)
DatabaseSession = Depends(get_db)
