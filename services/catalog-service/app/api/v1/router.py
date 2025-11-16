"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import movies

router = APIRouter()

router.include_router(movies.router, prefix="/movies", tags=["Movies"])
