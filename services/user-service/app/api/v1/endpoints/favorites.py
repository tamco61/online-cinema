"""Favorites endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService, get_cache_service
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.favorites import FavoriteResponse
from app.services.favorites_service import FavoritesService
from app.services.user_service import UserService

router = APIRouter()


async def get_favorites_service(
    db: AsyncSession = Depends(get_db),
) -> FavoritesService:
    """Dependency for favorites service."""
    return FavoritesService(db)


async def get_user_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
) -> UserService:
    """Dependency for user service."""
    return UserService(db, cache)


@router.get("/me/favorites", response_model=list[FavoriteResponse], tags=["Favorites"])
async def get_favorites(
    limit: int = Query(default=100, ge=1, le=500),
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    favorites_service: FavoritesService = Depends(get_favorites_service),
):
    """
    Get user favorites.

    Returns user's favorite/bookmarked content.
    """
    # Ensure profile exists
    profile = await user_service.get_or_create_profile(user_id)

    # Get favorites
    favorites = await favorites_service.get_user_favorites(profile.id, limit=limit)

    return [FavoriteResponse.model_validate(f) for f in favorites]


@router.post(
    "/me/favorites/{content_id}",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Favorites"],
)
async def add_to_favorites(
    content_id: uuid.UUID,
    content_type: str = Query(..., description="Content type: movie, series, etc."),
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    favorites_service: FavoritesService = Depends(get_favorites_service),
):
    """
    Add content to favorites.

    Returns the created favorite entry.
    """
    # Ensure profile exists
    profile = await user_service.get_or_create_profile(user_id)

    # Add to favorites
    favorite = await favorites_service.add_favorite(
        profile.id, content_id, content_type
    )

    return FavoriteResponse.model_validate(favorite)


@router.delete(
    "/me/favorites/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Favorites"],
)
async def remove_from_favorites(
    content_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    favorites_service: FavoritesService = Depends(get_favorites_service),
):
    """
    Remove content from favorites.

    Returns 204 No Content on success.
    """
    # Ensure profile exists
    profile = await user_service.get_or_create_profile(user_id)

    # Remove from favorites
    await favorites_service.remove_favorite(profile.id, content_id)

    return None
