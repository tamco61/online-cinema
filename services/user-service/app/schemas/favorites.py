"""Pydantic schemas for favorites."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FavoriteBase(BaseModel):
    """Base favorite schema."""

    content_id: uuid.UUID
    content_type: str = Field(..., max_length=20)


class FavoriteCreate(FavoriteBase):
    """Schema for adding to favorites."""

    pass


class FavoriteResponse(FavoriteBase):
    """Favorite response schema."""

    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
