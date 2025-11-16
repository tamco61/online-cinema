"""
Middleware components for Cinema microservices.
"""

from .correlation_id import CorrelationIdMiddleware, get_correlation_id
from .error_handler import ErrorHandlerMiddleware, setup_error_handlers
from .rate_limiter import RateLimiterMiddleware

__all__ = [
    "CorrelationIdMiddleware",
    "get_correlation_id",
    "ErrorHandlerMiddleware",
    "setup_error_handlers",
    "RateLimiterMiddleware",
]
