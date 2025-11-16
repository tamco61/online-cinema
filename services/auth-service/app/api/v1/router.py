"""
API v1 router.

Aggregates all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, oauth

# Create main v1 router
api_router = APIRouter()

# Include auth endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Include OAuth endpoints
api_router.include_router(
    oauth.router,
    prefix="/auth/oauth",
    tags=["OAuth"],
)
