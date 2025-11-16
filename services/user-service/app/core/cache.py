"""Redis cache service."""

import json
import uuid
from typing import Any, Optional

from redis import asyncio as aioredis

from app.core.config import settings


class CacheService:
    """Redis cache service for user profiles."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if not self._initialized:
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

    async def get_profile(self, user_id: uuid.UUID) -> Optional[dict]:
        """Get cached user profile."""
        if not settings.ENABLE_CACHE or not self._initialized:
            return None
        key = f"profile:{user_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_profile(self, user_id: uuid.UUID, profile: dict) -> None:
        """Cache user profile."""
        if not settings.ENABLE_CACHE or not self._initialized:
            return
        key = f"profile:{user_id}"
        await self.redis.setex(
            key,
            settings.REDIS_CACHE_TTL,
            json.dumps(profile, default=str),
        )

    async def delete_profile(self, user_id: uuid.UUID) -> None:
        """Delete cached profile."""
        if not self._initialized:
            return
        key = f"profile:{user_id}"
        await self.redis.delete(key)


cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dependency for cache service."""
    if not cache_service._initialized:
        await cache_service.initialize()
    return cache_service
