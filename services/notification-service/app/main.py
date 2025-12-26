from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import settings
from app.api.v1.endpoints import notifications
from app.kafka.consumer import NotificationEventConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global Kafka consumer instance
kafka_consumer: NotificationEventConsumer | None = None
consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler

    Startup:
    - Start Kafka consumer

    Shutdown:
    - Stop Kafka consumer
    """
    global kafka_consumer, consumer_task

    # Startup
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")

    try:
        # Start Kafka consumer if enabled
        if settings.ENABLE_KAFKA:
            kafka_consumer = NotificationEventConsumer()
            consumer_task = asyncio.create_task(kafka_consumer.start())
            logger.info("✅ Kafka consumer started")
        else:
            logger.warning("⚠️  Kafka consumer is disabled")

        logger.info(f"✅ {settings.SERVICE_NAME} started successfully")
        logger.info(f"   API Docs: http://{settings.HOST}:{settings.PORT}/docs")

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

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

    logger.info(f"✅ {settings.SERVICE_NAME} shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Notification Service",
    description="Notification service for online cinema platform with Email (SendGrid/AWS SES) and Push (FCM) support",
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
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)


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
    from app.providers.email import get_email_provider
    from app.providers.push import get_push_provider

    email_provider = get_email_provider()
    push_provider = get_push_provider()

    email_status = "healthy" if email_provider.validate_configuration() else "misconfigured"
    push_status = "healthy" if push_provider.validate_configuration() else "misconfigured"
    kafka_status = "enabled" if settings.ENABLE_KAFKA else "disabled"

    overall_status = "healthy" if email_status == "healthy" or push_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "email": email_status,
        "push": push_status,
        "kafka": kafka_status
    }

from fastapi.responses import PlainTextResponse
import yaml

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    openapi_dict = app.openapi()
    yaml_content = yaml.dump(openapi_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return PlainTextResponse(yaml_content, media_type="text/yaml")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
