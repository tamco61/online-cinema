from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.core.config import settings
from app.core.elasticsearch_client import es_client
from app.core.cache import cache
from app.api.v1.endpoints.search import router as search_router
from app.kafka_consumer.consumer import MovieEventConsumer
from app.services.search_service import SearchService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global consumer task
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global consumer_task

    # Startup
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")

    # Connect to Elasticsearch
    await es_client.connect()

    # Connect to Redis
    await cache.connect()

    # Start Kafka consumer in background
    if settings.ENABLE_KAFKA:
        search_service = SearchService(es_client.get_client(), cache)
        consumer = MovieEventConsumer(search_service)
        consumer_task = asyncio.create_task(consumer.start())
        logger.info("📨 Kafka consumer started in background")

    logger.info(f"✅ {settings.SERVICE_NAME} started successfully")

    yield

    # Shutdown
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")

    # Stop Kafka consumer
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("📭 Kafka consumer stopped")

    # Close connections
    await es_client.close()
    await cache.close()

    logger.info(f"👋 {settings.SERVICE_NAME} shut down complete")


# Create FastAPI app
app = FastAPI(
    title="Search Service",
    description="Full-text search service for online cinema using Elasticsearch",
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
app.include_router(search_router, prefix=settings.API_V1_PREFIX)


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
    es_healthy = False
    redis_healthy = False

    try:
        es_healthy = await es_client.get_client().ping()
    except:
        pass

    try:
        if cache.redis:
            await cache.redis.ping()
            redis_healthy = True
    except:
        pass

    return {
        "status": "healthy" if (es_healthy and redis_healthy) else "degraded",
        "elasticsearch": "ok" if es_healthy else "error",
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
