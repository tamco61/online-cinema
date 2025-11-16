"""
Auth Service - Main application.

FastAPI application for authentication and authorization.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import close_db, init_db
from app.services.redis_service import redis_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles:
    - Database initialization
    - Redis connection setup
    - Cleanup on shutdown
    """
    # Startup
    print(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")

    # Initialize Redis
    await redis_service.initialize()
    print("✓ Redis connected")

    # Initialize database (for development only - use migrations in production)
    if settings.is_development:
        await init_db()
        print("✓ Database initialized (development mode)")

    yield

    # Shutdown
    print("Shutting down...")
    await redis_service.close()
    await close_db()
    print("✓ Connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="Authentication and authorization service for online cinema platform",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and version.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.

    Returns service information.
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "docs": "/docs" if settings.ENABLE_API_DOCS else "disabled",
    }


# Include API routers
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
