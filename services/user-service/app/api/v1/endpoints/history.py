"""Watch history endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService, get_cache_service
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.history import WatchHistoryResponse, WatchHistoryUpdate
from app.services.history_service import HistoryService
from app.services.user_service import UserService

router = APIRouter()


async def get_history_service(db: AsyncSession = Depends(get_db)) -> HistoryService:
    """Dependency for history service."""
    return HistoryService(db)


async def get_user_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
) -> UserService:
    """Dependency for user service."""
    return UserService(db, cache)


@router.get("/me/history", response_model=list[WatchHistoryResponse], tags=["History"])
async def get_watch_history(
    limit: int = Query(default=50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    history_service: HistoryService = Depends(get_history_service),
):
    """
    Get user watch history.

    Returns recently watched content ordered by last watched time.
    """
    # Ensure profile exists
    profile = await user_service.get_or_create_profile(user_id)

    # Get history
    history = await history_service.get_user_history(profile.id, limit=limit)

    return [WatchHistoryResponse.model_validate(h) for h in history]


@router.post("/me/history", response_model=WatchHistoryResponse, tags=["History"])
async def update_watch_progress(
    progress_data: WatchHistoryUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    history_service: HistoryService = Depends(get_history_service),
):
    """
    Update watch progress for content.

    Creates new history entry if doesn't exist, updates if exists.
    """
    # Ensure profile exists
    profile = await user_service.get_or_create_profile(user_id)

    # Update progress
    history = await history_service.update_progress(profile.id, progress_data)

    return WatchHistoryResponse.model_validate(history)
