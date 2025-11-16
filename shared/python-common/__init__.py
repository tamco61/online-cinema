"""
Cinema Common Library - Shared components for Cinema microservices.

This library provides common functionality for all Cinema microservices:
- Middleware (correlation ID, error handling, rate limiting)
- Structured logging with JSON formatting
- Prometheus metrics integration
- OpenTelemetry distributed tracing
- Custom exceptions

Example:
    ```python
    from fastapi import FastAPI
    from cinema_common import setup_application

    app = FastAPI()
    setup_application(
        app=app,
        service_name="catalog-service",
        service_version="1.0.0"
    )
    ```
"""

from .middleware import (
    CorrelationIdMiddleware,
    ErrorHandlerMiddleware,
    RateLimiterMiddleware,
    get_correlation_id,
    set_correlation_id,
    setup_error_handlers,
)
from .middleware.error_handler import (
    BadRequestException,
    CinemaException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
)
from .utils import get_logger, setup_logging, setup_metrics, setup_tracing

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Middleware
    "CorrelationIdMiddleware",
    "ErrorHandlerMiddleware",
    "RateLimiterMiddleware",
    "get_correlation_id",
    "set_correlation_id",
    "setup_error_handlers",
    # Exceptions
    "CinemaException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "BadRequestException",
    "ConflictException",
    "ServiceUnavailableException",
    # Utils
    "get_logger",
    "setup_logging",
    "setup_metrics",
    "setup_tracing",
    # Setup helper
    "setup_application",
]


def setup_application(
    app,
    service_name: str,
    service_version: str = "1.0.0",
    log_level: str = "INFO",
    environment: str = "development",
    enable_metrics: bool = True,
    enable_tracing: bool = True,
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    enable_rate_limiting: bool = False,
    requests_per_minute: int = 60,
):
    """
    Setup all common components for a FastAPI application.

    This is a convenience function that configures:
    - Structured logging
    - Error handlers
    - Correlation ID middleware
    - Prometheus metrics
    - Distributed tracing
    - Optional rate limiting

    Args:
        app: FastAPI application instance
        service_name: Name of the microservice
        service_version: Service version
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        environment: Deployment environment (development, staging, production)
        enable_metrics: Enable Prometheus metrics (default: True)
        enable_tracing: Enable distributed tracing (default: True)
        jaeger_host: Jaeger agent hostname
        jaeger_port: Jaeger agent port
        enable_rate_limiting: Enable rate limiting middleware (default: False)
        requests_per_minute: Rate limit threshold

    Returns:
        Configured FastAPI application

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common import setup_application

        app = FastAPI(title="Catalog Service")

        setup_application(
            app=app,
            service_name="catalog-service",
            service_version="1.0.0",
            log_level="INFO",
            environment="production",
            enable_metrics=True,
            enable_tracing=True
        )
        ```
    """
    # Setup logging
    setup_logging(
        service_name=service_name,
        service_version=service_version,
        log_level=log_level,
        environment=environment,
        json_logs=(environment != "development"),
    )

    logger = get_logger(__name__)
    logger.info(f"Setting up {service_name} v{service_version}")

    # Setup error handlers
    setup_error_handlers(app)

    # Add correlation ID middleware
    app.add_middleware(CorrelationIdMiddleware)

    # Setup metrics
    if enable_metrics:
        setup_metrics(app, service_name=service_name)

    # Setup tracing
    if enable_tracing:
        setup_tracing(
            app=app,
            service_name=service_name,
            service_version=service_version,
            jaeger_host=jaeger_host,
            jaeger_port=jaeger_port,
            environment=environment,
        )

    # Optional: Rate limiting
    if enable_rate_limiting:
        app.add_middleware(
            RateLimiterMiddleware,
            requests_per_minute=requests_per_minute,
        )

    logger.info(
        f"{service_name} setup complete",
        extra={
            "version": service_version,
            "environment": environment,
            "metrics_enabled": enable_metrics,
            "tracing_enabled": enable_tracing,
            "rate_limiting_enabled": enable_rate_limiting,
        },
    )

    return app
