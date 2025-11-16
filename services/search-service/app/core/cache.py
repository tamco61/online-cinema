import redis.asyncio as redis
from app.core.config import settings
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis: redis.Redis | None = None

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Redis connection error: {e}")
            if settings.ENABLE_CACHE:
                raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("🔌 Redis connection closed")

    async def get_search_results(self, query_hash: str) -> dict | None:
        """Get cached search results by query hash"""
        if not settings.ENABLE_CACHE or not self.redis:
            return None

        try:
            key = f"search:query:{query_hash}"
            cached = await self.redis.get(key)

            if cached:
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(cached)

            logger.debug(f"❌ Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set_search_results(self, query_hash: str, results: dict):
        """Cache search results"""
        if not settings.ENABLE_CACHE or not self.redis:
            return

        try:
            key = f"search:query:{query_hash}"
            await self.redis.setex(
                key,
                settings.REDIS_CACHE_TTL,
                json.dumps(results)
            )
            logger.debug(f"💾 Cached: {key}")
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def invalidate_movie(self, movie_id: str):
        """Invalidate all search caches (simple approach - delete all search keys)"""
        if not settings.ENABLE_CACHE or not self.redis:
            return

        try:
            # Delete all search cache keys
            cursor = 0
            pattern = "search:query:*"

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                    logger.debug(f"🗑️  Invalidated {len(keys)} search cache keys")

                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    @staticmethod
    def generate_query_hash(query: str, filters: dict) -> str:
        """Generate hash from query and filters"""
        query_string = f"{query}_{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(query_string.encode()).hexdigest()


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Dependency to get cache instance"""
    return cache
