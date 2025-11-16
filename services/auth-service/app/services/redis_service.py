"""
Redis service for managing refresh tokens and sessions.
"""

import uuid
from datetime import timedelta
from typing import Optional

from redis import asyncio as aioredis

from app.core.config import settings


class RedisService:
    """
    Service for managing refresh tokens in Redis.

    Refresh tokens are stored with keys like:
    auth:refresh:<user_id>:<token_id>

    This allows:
    - Multiple active sessions per user
    - Easy token invalidation
    - Automatic expiration via Redis TTL
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """
        Initialize Redis service.

        Args:
            redis_client: Redis client instance (optional, will create if not provided)
        """
        self.redis = redis_client
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if not self._initialized:
            if self.redis is None:
                self.redis = await aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            self._initialized = True

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis and self._initialized:
            await self.redis.close()
            self._initialized = False

    def _get_refresh_token_key(self, user_id: uuid.UUID, token_id: str) -> str:
        """
        Generate Redis key for refresh token.

        Args:
            user_id: User ID
            token_id: Unique token identifier

        Returns:
            Redis key string
        """
        return f"auth:refresh:{str(user_id)}:{token_id}"

    def _get_user_tokens_pattern(self, user_id: uuid.UUID) -> str:
        """
        Generate pattern to match all tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Redis key pattern
        """
        return f"auth:refresh:{str(user_id)}:*"

    async def store_refresh_token(
        self,
        user_id: uuid.UUID,
        token_id: str,
        token_value: str,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Store refresh token in Redis.

        Args:
            user_id: User ID
            token_id: Unique token identifier
            token_value: Actual token string
            ttl: Time to live (default: 7 days from settings)

        Returns:
            True if stored successfully
        """
        if not self._initialized:
            await self.initialize()

        key = self._get_refresh_token_key(user_id, token_id)

        if ttl is None:
            ttl = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        # Store token with expiration
        await self.redis.setex(
            key,
            int(ttl.total_seconds()),
            token_value,
        )

        return True

    async def get_refresh_token(
        self,
        user_id: uuid.UUID,
        token_id: str,
    ) -> Optional[str]:
        """
        Retrieve refresh token from Redis.

        Args:
            user_id: User ID
            token_id: Token identifier

        Returns:
            Token value if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        key = self._get_refresh_token_key(user_id, token_id)
        return await self.redis.get(key)

    async def delete_refresh_token(
        self,
        user_id: uuid.UUID,
        token_id: str,
    ) -> bool:
        """
        Delete specific refresh token.

        Args:
            user_id: User ID
            token_id: Token identifier

        Returns:
            True if deleted, False if not found
        """
        if not self._initialized:
            await self.initialize()

        key = self._get_refresh_token_key(user_id, token_id)
        deleted = await self.redis.delete(key)
        return deleted > 0

    async def delete_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """
        Delete all refresh tokens for a user (logout from all devices).

        Args:
            user_id: User ID

        Returns:
            Number of tokens deleted
        """
        if not self._initialized:
            await self.initialize()

        pattern = self._get_user_tokens_pattern(user_id)

        # Find all matching keys
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        # Delete all found keys
        if keys:
            return await self.redis.delete(*keys)

        return 0

    async def verify_refresh_token(
        self,
        user_id: uuid.UUID,
        token_id: str,
        token_value: str,
    ) -> bool:
        """
        Verify that a refresh token is valid and matches stored value.

        Args:
            user_id: User ID
            token_id: Token identifier
            token_value: Token value to verify

        Returns:
            True if token is valid, False otherwise
        """
        stored_value = await self.get_refresh_token(user_id, token_id)

        if stored_value is None:
            return False

        return stored_value == token_value

    async def get_user_active_sessions_count(self, user_id: uuid.UUID) -> int:
        """
        Get number of active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active refresh tokens
        """
        if not self._initialized:
            await self.initialize()

        pattern = self._get_user_tokens_pattern(user_id)

        count = 0
        async for _ in self.redis.scan_iter(match=pattern):
            count += 1

        return count


# Global Redis service instance
redis_service = RedisService()


async def get_redis_service() -> RedisService:
    """
    Dependency for getting Redis service.

    Returns:
        Initialized Redis service instance
    """
    if not redis_service._initialized:
        await redis_service.initialize()

    return redis_service
