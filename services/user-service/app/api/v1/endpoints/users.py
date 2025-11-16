"""User profile endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService, get_cache_service
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.user_service import UserService

router = APIRouter()


async def get_user_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
) -> UserService:
    """Dependency for user service."""
    return UserService(db, cache)


@router.get("/me", response_model=UserProfileResponse, tags=["Users"])
async def get_my_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user profile.

    Creates profile automatically if doesn't exist.
    """
    profile = await user_service.get_or_create_profile(user_id)
    return UserProfileResponse.model_validate(profile)


@router.patch("/me", response_model=UserProfileResponse, tags=["Users"])
async def update_my_profile(
    profile_data: UserProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user profile.

    Updates only provided fields.
    """
    profile = await user_service.update_profile(user_id, profile_data)
    return UserProfileResponse.model_validate(profile)
