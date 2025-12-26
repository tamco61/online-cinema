from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import redis_client
from app.api.v1.endpoints import payments

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler

    Startup:
    - Initialize database tables
    - Connect to Redis

    Shutdown:
    - Close Redis connection
    """
    # Startup
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")

    try:
        # Initialize database
        init_db()
        logger.info("✅ Database initialized")

        # Connect to Redis
        redis_client.connect()
        logger.info("✅ Redis connected")

        logger.info(f"✅ {settings.SERVICE_NAME} started successfully")
        logger.info(f"   API Docs: http://{settings.HOST}:{settings.PORT}/docs")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info(f"🔌 Shutting down {settings.SERVICE_NAME}...")

    try:
        # Close Redis connection
        redis_client.close()
        logger.info("✅ Redis connection closed")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

    logger.info(f"✅ {settings.SERVICE_NAME} shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Payment Service",
    description="Payment processing service for online cinema platform with YooMoney integration",
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
app.include_router(payments.router, prefix=settings.API_V1_PREFIX)


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
        # Check Redis connection
        redis_client.client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"

    # Check database connection
    try:
        from app.core.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    overall_status = "healthy" if redis_status == "healthy" and db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status
    }


@app.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": plan_id,
                "name": plan["name"],
                "price": plan["price"],
                "currency": settings.DEFAULT_CURRENCY,
                "duration_days": plan["duration_days"],
                "duration_text": f"{plan['duration_days']} дней"
            }
            for plan_id, plan in settings.PLANS.items()
        ]
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
