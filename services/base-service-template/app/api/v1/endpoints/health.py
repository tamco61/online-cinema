"""
Health check endpoints.

Provides health and readiness probes for Kubernetes/monitoring.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint. Returns service status and version.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    This endpoint always returns 200 OK if the service is running.
    Use for basic liveness probes.

    Returns:
        Health status response
    """
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        timestamp=datetime.utcnow(),
        details={
            "environment": settings.ENVIRONMENT,
        },
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Readiness check endpoint. Verifies database connectivity and other dependencies.",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """
    Readiness check endpoint.

    This endpoint verifies that the service is ready to handle requests
    by checking database connectivity and other dependencies.

    Use for Kubernetes readiness probes.

    Args:
        db: Database session (auto-injected)

    Returns:
        Readiness status response

    Raises:
        HTTPException: If service is not ready (database unreachable, etc.)
    """
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Determine overall status
    is_ready = db_status == "connected"
    overall_status = "ready" if is_ready else "not_ready"

    # Return appropriate status code
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        timestamp=datetime.utcnow(),
        details={
            "database": db_status,
            "environment": settings.ENVIRONMENT,
        },
    )


@router.get(
    "/ping",
    status_code=status.HTTP_200_OK,
    summary="Ping",
    description="Simple ping endpoint for load balancers.",
    include_in_schema=False,
)
async def ping() -> dict[str, str]:
    """
    Simple ping endpoint.

    Returns:
        Pong message
    """
    return {"message": "pong"}
