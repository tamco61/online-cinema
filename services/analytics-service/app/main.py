from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import settings
from app.core.clickhouse_client import ch_client
from app.api.v1.endpoints import analytics
from app.kafka_consumer.consumer import ViewingEventsConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global Kafka consumer instance
kafka_consumer: ViewingEventsConsumer | None = None
consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler

    Startup:
    - Initialize ClickHouse connection
    - Create database and tables
    - Start Kafka consumer

    Shutdown:
    - Stop Kafka consumer
    - Close ClickHouse connection
    """
    global kafka_consumer, consumer_task

    # Startup
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")

    try:
        # Initialize ClickHouse
        ch_client.ensure_database()
        ch_client.connect()
        ch_client.ensure_tables()
        logger.info("✅ ClickHouse initialized successfully")

        # Start Kafka consumer if enabled
        if settings.ENABLE_KAFKA:
            kafka_consumer = ViewingEventsConsumer(ch_client)
            consumer_task = asyncio.create_task(kafka_consumer.start())
            logger.info("✅ Kafka consumer started")
        else:
            logger.warning("⚠️  Kafka consumer is disabled")

        logger.info(f"✅ {settings.SERVICE_NAME} started successfully")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info(f"🔌 Shutting down {settings.SERVICE_NAME}...")

    try:
        # Stop Kafka consumer
        if kafka_consumer:
            await kafka_consumer.stop()
            logger.info("✅ Kafka consumer stopped")

        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        # Close ClickHouse connection
        ch_client.close()
        logger.info("✅ ClickHouse connection closed")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

    logger.info(f"✅ {settings.SERVICE_NAME} shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Analytics Service",
    description="Analytics service for online cinema platform. Collects and analyzes viewing events.",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check ClickHouse connection
        ch_client.execute("SELECT 1")
        ch_status = "healthy"
    except Exception as e:
        logger.error(f"ClickHouse health check failed: {e}")
        ch_status = "unhealthy"

    kafka_status = "enabled" if settings.ENABLE_KAFKA else "disabled"

    return {
        "status": "healthy" if ch_status == "healthy" else "degraded",
        "clickhouse": ch_status,
        "kafka": kafka_status
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
