from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.s3_client import s3_client
from app.core.cache import cache
from app.core.kafka_producer import kafka_producer
from app.api.v1.endpoints.streaming import router as streaming_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")

    # Connect to S3/MinIO
    s3_client.connect()

    # Connect to Redis
    await cache.connect()

    # Start Kafka producer
    await kafka_producer.start()

    logger.info(f"✅ {settings.SERVICE_NAME} started successfully")

    yield

    # Shutdown
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")

    # Stop Kafka producer
    await kafka_producer.stop()

    # Close Redis connection
    await cache.close()

    logger.info(f"👋 {settings.SERVICE_NAME} shut down complete")


# Create FastAPI app
app = FastAPI(
    title="Streaming Service",
    description="Video streaming service with S3/MinIO, signed URLs, and watch progress tracking",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(streaming_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    s3_healthy = False
    redis_healthy = False

    try:
        # Check S3
        s3_client.client.list_buckets()
        s3_healthy = True
    except:
        pass

    try:
        # Check Redis
        if cache.redis:
            await cache.redis.ping()
            redis_healthy = True
    except:
        pass

    return {
        "status": "healthy" if (s3_healthy and redis_healthy) else "degraded",
        "s3": "ok" if s3_healthy else "error",
        "redis": "ok" if redis_healthy else "error",
        "kafka": "enabled" if settings.ENABLE_KAFKA else "disabled"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
