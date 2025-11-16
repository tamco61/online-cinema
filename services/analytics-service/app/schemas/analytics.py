from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ViewingEventCreate(BaseModel):
    """Schema for creating viewing event via HTTP"""
    user_id: str = Field(..., description="User UUID")
    movie_id: str = Field(..., description="Movie UUID")
    event_type: str = Field(..., description="Event type: start, progress, finish")
    position_seconds: int = Field(0, ge=0, description="Playback position in seconds")
    session_id: Optional[str] = Field(None, description="Session UUID")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class PopularContentItem(BaseModel):
    """Popular content item"""
    movie_id: str
    total_views: int
    unique_viewers: int
    completion_rate: Optional[float] = None

    class Config:
        from_attributes = True


class PopularContentResponse(BaseModel):
    """Response with popular content"""
    items: list[PopularContentItem]
    period_days: int
    total_items: int


class UserStatsResponse(BaseModel):
    """User viewing statistics"""
    user_id: str
    movies_started: int
    movies_finished: int
    unique_movies_watched: int
    total_watch_time_seconds: int
    completion_rate: float
    period_days: int
    most_watched_movie_id: Optional[str] = None

    class Config:
        from_attributes = True
