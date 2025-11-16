"""
Correlation ID Middleware for request tracing across microservices.

This middleware:
- Extracts or generates a unique correlation ID for each request
- Propagates it through the request lifecycle
- Adds it to response headers
- Makes it available for logging and tracing
"""

import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for storing correlation ID
_correlation_id_ctx_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for distributed tracing.

    The correlation ID is:
    1. Extracted from X-Correlation-ID header if present
    2. Generated as a new UUID if not present
    3. Added to response headers
    4. Stored in context for access in logging/tracing

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common.middleware import CorrelationIdMiddleware

        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)
        ```
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Correlation-ID",
        generate_if_missing: bool = True,
    ):
        """
        Initialize the middleware.

        Args:
            app: FastAPI application instance
            header_name: Name of the correlation ID header (default: X-Correlation-ID)
            generate_if_missing: Generate new UUID if header is missing (default: True)
        """
        super().__init__(app)
        self.header_name = header_name
        self.generate_if_missing = generate_if_missing

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and inject correlation ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in the chain

        Returns:
            HTTP response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get(self.header_name)

        if not correlation_id and self.generate_if_missing:
            correlation_id = str(uuid.uuid4())

        # Store in context variable
        _correlation_id_ctx_var.set(correlation_id)

        # Add to request state for easy access
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        if correlation_id:
            response.headers[self.header_name] = correlation_id

        return response


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Current correlation ID or None if not set

    Example:
        ```python
        from cinema_common.middleware import get_correlation_id

        correlation_id = get_correlation_id()
        logger.info("Processing request", extra={"correlation_id": correlation_id})
        ```
    """
    return _correlation_id_ctx_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Manually set the correlation ID (useful for background tasks).

    Args:
        correlation_id: Correlation ID to set

    Example:
        ```python
        from cinema_common.middleware import set_correlation_id

        # In a background task
        set_correlation_id("task-123")
        ```
    """
    _correlation_id_ctx_var.set(correlation_id)
