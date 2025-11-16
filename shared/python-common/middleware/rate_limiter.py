"""
Rate Limiting Middleware for API protection.

Supports:
- In-memory rate limiting (for development/single instance)
- Redis-backed rate limiting (for production/distributed)
- Configurable limits per endpoint
- Different strategies: fixed window, sliding window
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Dict, Optional, Tuple

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from .error_handler import CinemaException


class RateLimitExceededException(CinemaException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )
        self.retry_after = retry_after


class RateLimiterBackend(ABC):
    """Abstract base class for rate limiter backends."""

    @abstractmethod
    async def is_allowed(
        self, key: str, limit: int, window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.

        Args:
            key: Rate limit key (e.g., IP address, user ID)
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining, reset_time)
        """
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        pass


class InMemoryRateLimiter(RateLimiterBackend):
    """
    In-memory rate limiter using fixed window strategy.

    WARNING: This is not suitable for production with multiple instances.
    Use RedisRateLimiter for distributed rate limiting.
    """

    def __init__(self):
        # Structure: {key: [(timestamp, count)]}
        self._requests: Dict[str, list] = defaultdict(list)

    async def is_allowed(
        self, key: str, limit: int, window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed (fixed window).

        Args:
            key: Rate limit key
            limit: Max requests per window
            window: Window size in seconds

        Returns:
            (is_allowed, remaining_requests, reset_timestamp)
        """
        now = time.time()
        window_start = now - window

        # Clean up old requests
        self._requests[key] = [
            (ts, count)
            for ts, count in self._requests[key]
            if ts > window_start
        ]

        # Count requests in current window
        current_count = sum(count for _, count in self._requests[key])

        # Check if allowed
        is_allowed = current_count < limit
        remaining = max(0, limit - current_count - 1) if is_allowed else 0

        # Add current request if allowed
        if is_allowed:
            self._requests[key].append((now, 1))

        # Calculate reset time (end of current window)
        reset_time = int(now + window)

        return is_allowed, remaining, reset_time

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if key in self._requests:
            del self._requests[key]


class RedisRateLimiter(RateLimiterBackend):
    """
    Redis-backed rate limiter using sliding window strategy.

    This implementation uses Redis sorted sets for accurate sliding windows.
    """

    def __init__(self, redis_client):
        """
        Initialize Redis rate limiter.

        Args:
            redis_client: Redis client instance (from redis-py or aioredis)
        """
        self.redis = redis_client

    async def is_allowed(
        self, key: str, limit: int, window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed (sliding window).

        Uses Redis sorted set with timestamps as scores.

        Args:
            key: Rate limit key
            limit: Max requests per window
            window: Window size in seconds

        Returns:
            (is_allowed, remaining_requests, reset_timestamp)
        """
        now = time.time()
        window_start = now - window
        redis_key = f"rate_limit:{key}"

        # Remove old entries
        await self.redis.zremrangebyscore(redis_key, 0, window_start)

        # Count requests in current window
        current_count = await self.redis.zcard(redis_key)

        # Check if allowed
        is_allowed = current_count < limit
        remaining = max(0, limit - current_count - 1) if is_allowed else 0

        # Add current request if allowed
        if is_allowed:
            await self.redis.zadd(redis_key, {str(now): now})
            # Set expiry on the key
            await self.redis.expire(redis_key, window)

        # Calculate reset time
        reset_time = int(now + window)

        return is_allowed, remaining, reset_time

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        redis_key = f"rate_limit:{key}"
        await self.redis.delete(redis_key)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.

    Supports both in-memory and Redis backends.

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common.middleware import RateLimiterMiddleware

        app = FastAPI()

        # In-memory (development)
        app.add_middleware(
            RateLimiterMiddleware,
            requests_per_minute=60,
            backend="memory"
        )

        # Redis (production)
        from redis import asyncio as aioredis
        redis_client = aioredis.from_url("redis://localhost:6379")

        app.add_middleware(
            RateLimiterMiddleware,
            requests_per_minute=100,
            backend="redis",
            redis_client=redis_client
        )
        ```
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: Optional[int] = None,
        backend: str = "memory",
        redis_client=None,
        key_func: Optional[Callable[[Request], str]] = None,
        excluded_paths: Optional[list] = None,
    ):
        """
        Initialize rate limiter middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute (default: 60)
            requests_per_hour: Max requests per hour (optional)
            backend: "memory" or "redis" (default: "memory")
            redis_client: Redis client (required if backend="redis")
            key_func: Function to extract rate limit key from request
            excluded_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.key_func = key_func or self._default_key_func
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]

        # Initialize backend
        if backend == "redis":
            if not redis_client:
                raise ValueError("redis_client is required when backend='redis'")
            self.backend = RedisRateLimiter(redis_client)
        else:
            self.backend = InMemoryRateLimiter()

    def _default_key_func(self, request: Request) -> str:
        """
        Default key function: use client IP.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Try to get real IP from X-Forwarded-For (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response (or 429 if rate limited)
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Get rate limit key
        key = self.key_func(request)

        # Check minute limit
        is_allowed, remaining, reset_time = await self.backend.is_allowed(
            key=f"{key}:minute",
            limit=self.requests_per_minute,
            window=60,
        )

        if not is_allowed:
            retry_after = reset_time - int(time.time())
            raise RateLimitExceededException(retry_after=retry_after)

        # Check hour limit (if configured)
        if self.requests_per_hour:
            is_allowed_hour, remaining_hour, reset_time_hour = await self.backend.is_allowed(
                key=f"{key}:hour",
                limit=self.requests_per_hour,
                window=3600,
            )

            if not is_allowed_hour:
                retry_after = reset_time_hour - int(time.time())
                raise RateLimitExceededException(retry_after=retry_after)

            # Use the more restrictive remaining count
            remaining = min(remaining, remaining_hour)
            reset_time = max(reset_time, reset_time_hour)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response


def rate_limit_dependency(
    requests_per_minute: int = 60,
    key_func: Optional[Callable[[Request], str]] = None,
):
    """
    Dependency for per-endpoint rate limiting.

    Example:
        ```python
        from fastapi import Depends, FastAPI
        from cinema_common.middleware import rate_limit_dependency

        app = FastAPI()

        @app.get("/api/expensive", dependencies=[Depends(rate_limit_dependency(10))])
        async def expensive_endpoint():
            return {"message": "Limited to 10 requests/minute"}
        ```
    """
    # This is a placeholder for a more sophisticated implementation
    # In practice, you'd want to integrate this with your rate limiter backend
    def dependency(request: Request):
        # Implementation would check rate limit here
        pass

    return dependency
