"""Catalog Service - Main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.core.cache import cache_service
from app.core.config import settings
from app.db.session import close_db, init_db
from app.services.kafka_producer import kafka_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    print(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    # Initialize services
    await cache_service.initialize()
    print("✓ Redis connected")

    await kafka_producer.initialize()
    if settings.ENABLE_KAFKA:
        print("✓ Kafka producer connected")

    if settings.is_development:
        await init_db()
        print("✓ Database initialized")

    yield

    # Shutdown
    await cache_service.close()
    await kafka_producer.close()
    await close_db()
    print("✓ Shutdown complete")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="Movie catalog service with Kafka events",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "kafka_enabled": settings.ENABLE_KAFKA,
    }


app.include_router(api_router.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
