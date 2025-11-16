"""
Authentication service with business logic.

Handles user registration, login, token refresh, and logout.
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.db.models import User
from app.schemas.auth import AuthResponse, TokenPair, TokenResponse, UserResponse
from app.services.jwt_service import JWTService
from app.services.redis_service import RedisService


class AuthService:
    """
    Authentication service.

    Provides methods for:
    - User registration
    - User login
    - Token refresh
    - User logout
    """

    def __init__(
        self,
        db: AsyncSession,
        jwt_service: JWTService,
        redis_service: RedisService,
    ):
        """
        Initialize auth service.

        Args:
            db: Database session
            jwt_service: JWT service for token operations
            redis_service: Redis service for refresh token storage
        """
        self.db = db
        self.jwt_service = jwt_service
        self.redis_service = redis_service

    async def register(
        self,
        email: str,
        password: str,
    ) -> AuthResponse:
        """
        Register a new user.

        Args:
            email: User email
            password: Plain text password

        Returns:
            AuthResponse with user info and tokens

        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password
        password_hash = get_password_hash(password)

        # Create new user
        new_user = User(
            email=email,
            password_hash=password_hash,
            is_active=True,
        )

        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Generate tokens
        tokens = await self._create_tokens_for_user(new_user.id)

        # Prepare response
        user_response = UserResponse.model_validate(new_user)
        return AuthResponse(user=user_response, tokens=tokens)

    async def login(
        self,
        email: str,
        password: str,
    ) -> AuthResponse:
        """
        Authenticate user and issue tokens.

        Args:
            email: User email
            password: Plain text password

        Returns:
            AuthResponse with user info and tokens

        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Generate tokens
        tokens = await self._create_tokens_for_user(user.id)

        # Prepare response
        user_response = UserResponse.model_validate(user)
        return AuthResponse(user=user_response, tokens=tokens)

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            TokenResponse with new access token

        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        # Verify refresh token
        token_data = self.jwt_service.verify_refresh_token(refresh_token)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id, token_id = token_data

        # Verify token exists in Redis
        is_valid = await self.redis_service.verify_refresh_token(
            user_id=user_id,
            token_id=token_id,
            token_value=refresh_token,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        # Check if user still exists and is active
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new access token
        access_token, expires_in = self.jwt_service.create_access_token(user_id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> bool:
        """
        Logout user by invalidating refresh token.

        Args:
            refresh_token: Refresh token to invalidate

        Returns:
            True if logout successful

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        token_data = self.jwt_service.verify_refresh_token(refresh_token)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id, token_id = token_data

        # Delete refresh token from Redis
        deleted = await self.redis_service.delete_refresh_token(
            user_id=user_id,
            token_id=token_id,
        )

        return deleted

    async def logout_all_sessions(
        self,
        user_id: uuid.UUID,
    ) -> int:
        """
        Logout user from all devices (invalidate all refresh tokens).

        Args:
            user_id: User ID

        Returns:
            Number of sessions invalidated
        """
        count = await self.redis_service.delete_all_user_tokens(user_id)
        return count

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def _create_tokens_for_user(
        self,
        user_id: uuid.UUID,
    ) -> TokenPair:
        """
        Create access and refresh tokens for user.

        Args:
            user_id: User ID

        Returns:
            TokenPair with access and refresh tokens
        """
        # Create access token
        access_token, access_expires_in = self.jwt_service.create_access_token(user_id)

        # Create refresh token
        refresh_token, token_id, refresh_expires_in = self.jwt_service.create_refresh_token(user_id)

        # Store refresh token in Redis
        await self.redis_service.store_refresh_token(
            user_id=user_id,
            token_id=token_id,
            token_value=refresh_token,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=access_expires_in,
        )


async def get_auth_service(
    db: AsyncSession,
    jwt_service: JWTService,
    redis_service: RedisService,
) -> AuthService:
    """
    Dependency for getting auth service.

    Args:
        db: Database session
        jwt_service: JWT service
        redis_service: Redis service

    Returns:
        AuthService instance
    """
    return AuthService(
        db=db,
        jwt_service=jwt_service,
        redis_service=redis_service,
    )
