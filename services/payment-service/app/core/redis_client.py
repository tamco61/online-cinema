import redis
from typing import Optional
import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for idempotency keys and caching"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test connection
            self.client.ping()
            logger.info("✅ Connected to Redis")

        except Exception as e:
            logger.error(f"❌ Redis connection error: {e}")
            raise

    def check_idempotency_key(self, key: str) -> Optional[dict]:
        """
        Check if idempotency key exists and return cached result

        Args:
            key: Idempotency key

        Returns:
            Cached result if exists, None otherwise
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")

        try:
            cached = self.client.get(f"idempotency:{key}")
            if cached:
                logger.info(f"🔄 Idempotency key hit: {key}")
                return json.loads(cached)
            return None

        except Exception as e:
            logger.error(f"Error checking idempotency key: {e}")
            return None

    def store_idempotency_key(self, key: str, result: dict, ttl: Optional[int] = None):
        """
        Store idempotency key with result

        Args:
            key: Idempotency key
            result: Result to cache
            ttl: Time to live in seconds (default from settings)
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")

        try:
            ttl = ttl or settings.IDEMPOTENCY_KEY_TTL
            self.client.setex(
                f"idempotency:{key}",
                ttl,
                json.dumps(result)
            )
            logger.debug(f"Stored idempotency key: {key}")

        except Exception as e:
            logger.error(f"Error storing idempotency key: {e}")

    def delete_idempotency_key(self, key: str):
        """Delete idempotency key"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")

        try:
            self.client.delete(f"idempotency:{key}")
            logger.debug(f"Deleted idempotency key: {key}")

        except Exception as e:
            logger.error(f"Error deleting idempotency key: {e}")

    def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set key-value pair"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")

        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)

        except Exception as e:
            logger.error(f"Error setting key: {e}")

    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")

        try:
            return self.client.get(key)

        except Exception as e:
            logger.error(f"Error getting key: {e}")
            return None

    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("🔌 Redis connection closed")


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client
