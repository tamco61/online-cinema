"""Pydantic schemas for watch history."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WatchHistoryBase(BaseModel):
    """Base watch history schema."""

    content_id: uuid.UUID
    content_type: str = Field(..., max_length=20)
    progress_seconds: int = Field(default=0, ge=0)
    duration_seconds: int | None = Field(None, ge=0)


class WatchHistoryCreate(WatchHistoryBase):
    """Schema for creating watch history entry."""

    pass


class WatchHistoryUpdate(BaseModel):
    """Schema for updating watch progress."""

    content_id: uuid.UUID
    content_type: str
    progress_seconds: int = Field(..., ge=0)
    duration_seconds: int | None = Field(None, ge=0)
    completed: bool = False


class WatchHistoryResponse(WatchHistoryBase):
    """Watch history response schema."""

    id: uuid.UUID
    profile_id: uuid.UUID
    completed: bool
    last_watched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
