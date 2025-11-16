"""User profile service."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService
from app.db.models import UserProfile
from app.schemas.user import UserProfileCreate, UserProfileResponse, UserProfileUpdate


class UserService:
    """Service for managing user profiles."""

    def __init__(self, db: AsyncSession, cache: CacheService):
        self.db = db
        self.cache = cache

    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> UserProfile | None:
        """Get profile by user_id (from auth-service)."""
        # Try cache first
        cached = await self.cache.get_profile(user_id)
        if cached:
            # Reconstruct profile from cache
            result = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            return result.scalar_one_or_none()

        # Query database
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        # Cache if found
        if profile:
            await self.cache.set_profile(
                user_id,
                {
                    "id": str(profile.id),
                    "user_id": str(profile.user_id),
                    "nickname": profile.nickname,
                    "avatar_url": profile.avatar_url,
                    "language": profile.language,
                    "country": profile.country,
                },
            )

        return profile

    async def create_profile(self, data: UserProfileCreate) -> UserProfile:
        """Create user profile."""
        # Check if profile already exists
        existing = await self.get_profile_by_user_id(data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists",
            )

        profile = UserProfile(
            user_id=data.user_id,
            nickname=data.nickname,
            avatar_url=data.avatar_url,
            language=data.language,
            country=data.country,
        )

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)

        # Cache the new profile
        await self.cache.set_profile(
            data.user_id,
            {
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "nickname": profile.nickname,
                "avatar_url": profile.avatar_url,
                "language": profile.language,
                "country": profile.country,
            },
        )

        return profile

    async def update_profile(
        self, user_id: uuid.UUID, data: UserProfileUpdate
    ) -> UserProfile:
        """Update user profile."""
        profile = await self.get_profile_by_user_id(user_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        # Update fields if provided
        if data.nickname is not None:
            profile.nickname = data.nickname
        if data.avatar_url is not None:
            profile.avatar_url = data.avatar_url
        if data.language is not None:
            profile.language = data.language
        if data.country is not None:
            profile.country = data.country

        await self.db.commit()
        await self.db.refresh(profile)

        # Invalidate cache
        await self.cache.delete_profile(user_id)

        return profile

    async def get_or_create_profile(self, user_id: uuid.UUID) -> UserProfile:
        """Get profile or create if doesn't exist."""
        profile = await self.get_profile_by_user_id(user_id)

        if not profile:
            # Create default profile
            profile_data = UserProfileCreate(user_id=user_id)
            profile = await self.create_profile(profile_data)

        return profile
