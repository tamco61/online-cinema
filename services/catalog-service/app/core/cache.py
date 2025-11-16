"""Redis cache service for movies."""

import json
import uuid
from typing import Any, Optional

from redis import asyncio as aioredis

from app.core.config import settings


class CacheService:
    """Redis cache service."""

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

    async def get_movie(self, movie_id: uuid.UUID) -> Optional[dict]:
        """Get cached movie details."""
        if not settings.ENABLE_CACHE or not self._initialized:
            return None
        key = f"movie:{movie_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_movie(self, movie_id: uuid.UUID, movie_data: dict) -> None:
        """Cache movie details."""
        if not settings.ENABLE_CACHE or not self._initialized:
            return
        key = f"movie:{movie_id}"
        await self.redis.setex(
            key,
            settings.REDIS_CACHE_TTL,
            json.dumps(movie_data, default=str),
        )

    async def delete_movie(self, movie_id: uuid.UUID) -> None:
        """Delete cached movie."""
        if not self._initialized:
            return
        key = f"movie:{movie_id}"
        await self.redis.delete(key)

    async def get_popular_movies(self) -> Optional[list]:
        """Get cached popular movies list."""
        if not settings.ENABLE_CACHE or not self._initialized:
            return None
        key = "movies:popular"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_popular_movies(self, movies: list) -> None:
        """Cache popular movies list."""
        if not settings.ENABLE_CACHE or not self._initialized:
            return
        key = "movies:popular"
        await self.redis.setex(
            key,
            settings.REDIS_CACHE_TTL,
            json.dumps(movies, default=str),
        )


cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dependency for cache service."""
    if not cache_service._initialized:
        await cache_service.initialize()
    return cache_service
