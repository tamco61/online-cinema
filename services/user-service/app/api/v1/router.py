"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import favorites, history, users

router = APIRouter()

# Include all endpoint routers
router.include_router(users.router, prefix="/users")
router.include_router(history.router, prefix="/users")
router.include_router(favorites.router, prefix="/users")
