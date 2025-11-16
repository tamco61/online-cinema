"""
Main router for API v1.

Combines all endpoint routers.
"""

from fastapi import APIRouter

from .endpoints import health

# Create main router for v1
router = APIRouter(prefix="/api/v1")

# Include endpoint routers
router.include_router(
    health.router,
    tags=["Health"],
)

# Add more routers here as you create endpoints
# Example:
# from .endpoints import movies
# router.include_router(
#     movies.router,
#     prefix="/movies",
#     tags=["Movies"],
# )
