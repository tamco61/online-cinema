"""User Service - Main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.core.cache import cache_service
from app.core.config import settings
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    print(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    await cache_service.initialize()
    print("✓ Redis connected")
    if settings.is_development:
        await init_db()
        print("✓ Database initialized")
    yield
    await cache_service.close()
    await close_db()
    print("✓ Shutdown complete")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="User profiles, subscriptions, watch history, and favorites",
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
    }


app.include_router(api_router.router, prefix="/api/v1")


from fastapi.responses import PlainTextResponse
import yaml

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    openapi_dict = app.openapi()
    yaml_content = yaml.dump(openapi_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return PlainTextResponse(yaml_content, media_type="text/yaml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
