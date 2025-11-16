"""Schemas module."""

from app.schemas.favorites import FavoriteCreate, FavoriteResponse
from app.schemas.history import (
    WatchHistoryCreate,
    WatchHistoryResponse,
    WatchHistoryUpdate,
)
from app.schemas.subscription import (
    PlanResponse,
    SubscriptionCreate,
    SubscriptionResponse,
)
from app.schemas.user import (
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
)

__all__ = [
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResponse",
    "PlanResponse",
    "SubscriptionCreate",
    "SubscriptionResponse",
    "WatchHistoryCreate",
    "WatchHistoryUpdate",
    "WatchHistoryResponse",
    "FavoriteCreate",
    "FavoriteResponse",
]
