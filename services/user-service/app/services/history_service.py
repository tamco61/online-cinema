"""Watch history service."""

import uuid
from datetime import datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile, WatchHistory
from app.schemas.history import WatchHistoryUpdate


class HistoryService:
    """Service for managing watch history."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_history(
        self, profile_id: uuid.UUID, limit: int = 50
    ) -> list[WatchHistory]:
        """Get user watch history, ordered by last watched."""
        result = await self.db.execute(
            select(WatchHistory)
            .where(WatchHistory.profile_id == profile_id)
            .order_by(desc(WatchHistory.last_watched_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_progress(
        self, profile_id: uuid.UUID, data: WatchHistoryUpdate
    ) -> WatchHistory:
        """Update watch progress for content."""
        # Find existing history entry
        result = await self.db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.profile_id == profile_id,
                    WatchHistory.content_id == data.content_id,
                )
            )
        )
        history = result.scalar_one_or_none()

        if history:
            # Update existing
            history.progress_seconds = data.progress_seconds
            history.duration_seconds = data.duration_seconds
            history.completed = data.completed
            history.last_watched_at = datetime.utcnow()
        else:
            # Create new entry
            history = WatchHistory(
                profile_id=profile_id,
                content_id=data.content_id,
                content_type=data.content_type,
                progress_seconds=data.progress_seconds,
                duration_seconds=data.duration_seconds,
                completed=data.completed,
                last_watched_at=datetime.utcnow(),
            )
            self.db.add(history)

        await self.db.commit()
        await self.db.refresh(history)
        return history

    async def get_content_progress(
        self, profile_id: uuid.UUID, content_id: uuid.UUID
    ) -> WatchHistory | None:
        """Get progress for specific content."""
        result = await self.db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.profile_id == profile_id,
                    WatchHistory.content_id == content_id,
                )
            )
        )
        return result.scalar_one_or_none()
