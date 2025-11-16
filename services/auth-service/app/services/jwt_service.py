"""
JWT service for creating and validating tokens.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt

from app.core.config import settings


class JWTService:
    """
    Service for managing JWT tokens.

    Handles creation and validation of access and refresh tokens.
    """

    def __init__(self):
        """Initialize JWT service."""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        user_id: uuid.UUID,
        additional_claims: Optional[dict[str, Any]] = None,
    ) -> tuple[str, int]:
        """
        Create JWT access token.

        Args:
            user_id: User ID to encode in token
            additional_claims: Additional claims to include

        Returns:
            Tuple of (token, expires_in_seconds)
        """
        now = datetime.utcnow()
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = now + expires_delta

        # Build token payload
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),  # Unique token ID
        }

        # Add additional claims if provided
        if additional_claims:
            payload.update(additional_claims)

        # Encode JWT
        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        # Calculate expiration time in seconds
        expires_in = int(expires_delta.total_seconds())

        return token, expires_in

    def create_refresh_token(
        self,
        user_id: uuid.UUID,
    ) -> tuple[str, str, int]:
        """
        Create refresh token.

        Args:
            user_id: User ID to encode in token

        Returns:
            Tuple of (token, token_id, expires_in_seconds)
        """
        now = datetime.utcnow()
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = now + expires_delta

        # Generate unique token ID
        token_id = str(uuid.uuid4())

        # Build token payload
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": now,
            "jti": token_id,
        }

        # Encode JWT
        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        # Calculate expiration time in seconds
        expires_in = int(expires_delta.total_seconds())

        return token, token_id, expires_in

    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Token payload

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except JWTError as e:
            raise JWTError(f"Token validation failed: {str(e)}")

    def verify_access_token(self, token: str) -> Optional[uuid.UUID]:
        """
        Verify access token and extract user ID.

        Args:
            token: Access token to verify

        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            payload = self.decode_token(token)

            # Verify token type
            if payload.get("type") != "access":
                return None

            # Extract user ID
            user_id = payload.get("sub")
            if not user_id:
                return None

            return uuid.UUID(user_id)

        except (JWTError, ValueError):
            return None

    def verify_refresh_token(self, token: str) -> Optional[tuple[uuid.UUID, str]]:
        """
        Verify refresh token and extract user ID and token ID.

        Args:
            token: Refresh token to verify

        Returns:
            Tuple of (user_id, token_id) if valid, None otherwise
        """
        try:
            payload = self.decode_token(token)

            # Verify token type
            if payload.get("type") != "refresh":
                return None

            # Extract user ID and token ID
            user_id = payload.get("sub")
            token_id = payload.get("jti")

            if not user_id or not token_id:
                return None

            return uuid.UUID(user_id), token_id

        except (JWTError, ValueError):
            return None

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """
        Get token expiration time.

        Args:
            token: JWT token

        Returns:
            Expiration datetime if token is valid, None otherwise
        """
        try:
            payload = self.decode_token(token)
            exp = payload.get("exp")

            if exp:
                return datetime.fromtimestamp(exp)

            return None

        except JWTError:
            return None


# Global JWT service instance
jwt_service = JWTService()


def get_jwt_service() -> JWTService:
    """
    Dependency for getting JWT service.

    Returns:
        JWT service instance
    """
    return jwt_service
