"""
Main FastAPI application.

This module creates and configures the FastAPI application with:
- Cinema-common library integration (logging, metrics, tracing)
- Middleware setup
- API routers
- Lifespan events
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.middleware import setup_middleware
from app.db.session import close_db, init_db

# Try to import cinema-common library
try:
    from cinema_common import get_logger, setup_logging, setup_metrics, setup_tracing

    CINEMA_COMMON_AVAILABLE = True
except ImportError:
    CINEMA_COMMON_AVAILABLE = False
    import logging

    logging.warning(
        "cinema-common library not found. "
        "Install with: pip install -e ../../shared/python-common"
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None (application runs during this time)
    """
    # Startup
    print(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    # Setup logging (if cinema-common is available)
    if CINEMA_COMMON_AVAILABLE:
        setup_logging(
            service_name=settings.SERVICE_NAME,
            service_version=settings.SERVICE_VERSION,
            log_level=settings.LOG_LEVEL,
            environment=settings.ENVIRONMENT,
            json_logs=settings.JSON_LOGS,
        )

        logger = get_logger(__name__)
        logger.info(
            f"{settings.SERVICE_NAME} starting up",
            extra={
                "version": settings.SERVICE_VERSION,
                "environment": settings.ENVIRONMENT,
            },
        )
    else:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info(f"{settings.SERVICE_NAME} starting up")

    # Initialize database (in production, use Alembic migrations)
    if settings.is_development:
        try:
            await init_db()
            if CINEMA_COMMON_AVAILABLE:
                logger.info("Database initialized")
        except Exception as e:
            if CINEMA_COMMON_AVAILABLE:
                logger.error(f"Failed to initialize database: {e}", exc_info=True)
            else:
                logger.error(f"Failed to initialize database: {e}")

    # Application is running
    yield

    # Shutdown
    if CINEMA_COMMON_AVAILABLE:
        logger.info(f"{settings.SERVICE_NAME} shutting down")
    else:
        logger.info(f"{settings.SERVICE_NAME} shutting down")

    # Close database connections
    await close_db()


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        description=f"{settings.SERVICE_NAME} API",
        docs_url="/docs" if settings.ENABLE_API_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
        lifespan=lifespan,
    )

    # Setup middleware
    setup_middleware(app)

    # Setup metrics (if cinema-common is available)
    if CINEMA_COMMON_AVAILABLE and settings.ENABLE_METRICS:
        setup_metrics(
            app=app,
            service_name=settings.SERVICE_NAME,
        )

    # Setup tracing (if cinema-common is available)
    if CINEMA_COMMON_AVAILABLE and settings.ENABLE_TRACING:
        setup_tracing(
            app=app,
            service_name=settings.SERVICE_NAME,
            service_version=settings.SERVICE_VERSION,
            jaeger_host=settings.JAEGER_HOST,
            jaeger_port=settings.JAEGER_PORT,
            environment=settings.ENVIRONMENT,
        )

    # Include API routers
    app.include_router(api_v1_router)

    # Root endpoint
    @app.get(
        "/",
        tags=["Root"],
        summary="Service information",
    )
    async def root() -> dict[str, str]:
        """
        Root endpoint with service information.

        Returns:
            Service metadata
        """
        return {
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "/docs" if settings.ENABLE_API_DOCS else "disabled",
        }

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
