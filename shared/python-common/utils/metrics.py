"""
Prometheus metrics integration for Cinema microservices.

Features:
- Automatic HTTP request metrics (latency, count, errors)
- Custom business metrics support
- Standard service metrics (CPU, memory, connections)
- /metrics endpoint for Prometheus scraping
"""

import time
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Standard HTTP Metrics
# =============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["service", "method", "endpoint"],
)

http_exceptions_total = Counter(
    "http_exceptions_total",
    "Total number of exceptions raised",
    ["service", "exception_type"],
)


# =============================================================================
# Database Metrics
# =============================================================================

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
    ["service", "database"],
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["service", "operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

db_errors_total = Counter(
    "db_errors_total",
    "Total database errors",
    ["service", "error_type"],
)


# =============================================================================
# Cache Metrics
# =============================================================================

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["service", "cache_name"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["service", "cache_name"],
)

cache_operation_duration_seconds = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["service", "operation"],
)


# =============================================================================
# Business Metrics (Examples)
# =============================================================================

business_events_total = Counter(
    "business_events_total",
    "Total business events",
    ["service", "event_type"],
)

active_users = Gauge(
    "active_users",
    "Number of currently active users",
    ["service"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP metrics for Prometheus.

    Automatically tracks:
    - Request count by endpoint, method, status
    - Request latency
    - Requests in progress
    - Exception counts

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common.utils.metrics import PrometheusMiddleware

        app = FastAPI()
        app.add_middleware(PrometheusMiddleware, service_name="catalog-service")
        ```
    """

    def __init__(self, app, service_name: str = "cinema-service"):
        """
        Initialize Prometheus middleware.

        Args:
            app: FastAPI application
            service_name: Service name for metric labels
        """
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract endpoint pattern (remove path parameters)
        endpoint = request.url.path
        method = request.method

        # Track in-progress requests
        http_requests_in_progress.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
        ).inc()

        # Measure request duration
        start_time = time.time()
        exception_type = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Record exception
            exception_type = type(e).__name__
            http_exceptions_total.labels(
                service=self.service_name,
                exception_type=exception_type,
            ).inc()
            raise
        finally:
            # Record request duration
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            # Decrement in-progress counter
            http_requests_in_progress.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint,
            ).dec()

        # Record total requests
        http_requests_total.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
            status=status_code,
        ).inc()

        return response


def setup_metrics(
    app: FastAPI,
    service_name: str,
    include_default_metrics: bool = True,
) -> None:
    """
    Setup Prometheus metrics for FastAPI application.

    Adds:
    - /metrics endpoint for Prometheus scraping
    - Automatic HTTP request metrics
    - Optional default system metrics

    Args:
        app: FastAPI application
        service_name: Service name for metric labels
        include_default_metrics: Include process/system metrics (default: True)

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common.utils import setup_metrics

        app = FastAPI()
        setup_metrics(app, service_name="catalog-service")
        ```
    """
    # Add metrics middleware
    app.add_middleware(PrometheusMiddleware, service_name=service_name)

    # Add /metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    logger.info(
        f"Prometheus metrics configured for {service_name}",
        extra={
            "metrics_endpoint": "/metrics",
            "include_default_metrics": include_default_metrics,
        },
    )


# =============================================================================
# Helper Functions for Custom Metrics
# =============================================================================


def track_cache_hit(service_name: str, cache_name: str) -> None:
    """
    Track a cache hit.

    Args:
        service_name: Service name
        cache_name: Name of the cache

    Example:
        ```python
        from cinema_common.utils.metrics import track_cache_hit

        result = await redis.get(key)
        if result:
            track_cache_hit("catalog-service", "movie_cache")
        ```
    """
    cache_hits_total.labels(service=service_name, cache_name=cache_name).inc()


def track_cache_miss(service_name: str, cache_name: str) -> None:
    """
    Track a cache miss.

    Args:
        service_name: Service name
        cache_name: Name of the cache
    """
    cache_misses_total.labels(service=service_name, cache_name=cache_name).inc()


def track_business_event(service_name: str, event_type: str) -> None:
    """
    Track a business event.

    Args:
        service_name: Service name
        event_type: Type of business event

    Example:
        ```python
        from cinema_common.utils.metrics import track_business_event

        # User started watching a movie
        track_business_event("streaming-service", "video_started")
        ```
    """
    business_events_total.labels(service=service_name, event_type=event_type).inc()


def set_active_users(service_name: str, count: int) -> None:
    """
    Set the number of active users.

    Args:
        service_name: Service name
        count: Number of active users
    """
    active_users.labels(service=service_name).set(count)


class MetricsContext:
    """
    Context manager for tracking operation duration.

    Example:
        ```python
        from cinema_common.utils.metrics import MetricsContext, db_query_duration_seconds

        async def get_movie(movie_id: int):
            with MetricsContext(db_query_duration_seconds, service="catalog", operation="select"):
                result = await db.execute(query)
            return result
        ```
    """

    def __init__(self, histogram: Histogram, **labels):
        """
        Initialize metrics context.

        Args:
            histogram: Prometheus histogram to track
            **labels: Labels for the metric
        """
        self.histogram = histogram
        self.labels = labels
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record duration."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.histogram.labels(**self.labels).observe(duration)
