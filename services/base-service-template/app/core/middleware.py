"""
Middleware configuration using cinema-common library.

This module sets up all common middleware components:
- Correlation ID tracking
- Error handling
- Rate limiting (optional)
- CORS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Import from cinema-common library
try:
    from cinema_common import (
        CorrelationIdMiddleware,
        RateLimiterMiddleware,
        setup_error_handlers,
    )

    CINEMA_COMMON_AVAILABLE = True
except ImportError:
    CINEMA_COMMON_AVAILABLE = False
    import warnings

    warnings.warn(
        "cinema-common library not found. "
        "Install with: pip install -e ../../shared/python-common"
    )

from .config import settings


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.

    Args:
        app: FastAPI application instance

    Example:
        ```python
        from fastapi import FastAPI
        from app.core.middleware import setup_middleware

        app = FastAPI()
        setup_middleware(app)
        ```
    """
    # CORS Middleware
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Trusted Host Middleware (production only)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # Configure with actual hosts in production
        )

    # Cinema Common Middleware
    if CINEMA_COMMON_AVAILABLE:
        # Correlation ID Middleware (should be first)
        app.add_middleware(CorrelationIdMiddleware)

        # Rate Limiting (optional)
        if settings.ENABLE_RATE_LIMITING:
            app.add_middleware(
                RateLimiterMiddleware,
                requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
                requests_per_hour=settings.RATE_LIMIT_PER_HOUR,
                backend="memory",  # Use Redis in production
            )

        # Error Handlers (should be set up after middleware)
        setup_error_handlers(app)
