"""Pydantic schemas for user profiles."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    """Base user profile schema."""

    nickname: Optional[str] = Field(None, max_length=100, description="User nickname")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    language: str = Field(default="en", max_length=10, description="ISO 639-1 language code")
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2 country code")


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile."""

    user_id: uuid.UUID = Field(..., description="User ID from auth-service")


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response."""

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
