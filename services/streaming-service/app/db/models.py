from sqlalchemy import String, Integer, DateTime, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


class WatchProgress(Base):
    """
    Watch progress tracking

    Stores user's watch progress for movies
    Synced periodically from Redis
    """
    __tablename__ = "watch_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    movie_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Progress in seconds
    position_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional metadata
    last_watched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<WatchProgress(user_id={self.user_id}, movie_id={self.movie_id}, position={self.position_seconds}s)>"


class StreamSession(Base):
    """
    Stream session tracking

    Tracks individual streaming sessions
    Used for analytics
    """
    __tablename__ = "stream_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    movie_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Session info
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Watch duration in seconds
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Client info (optional)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self):
        return f"<StreamSession(user_id={self.user_id}, movie_id={self.movie_id}, started={self.started_at})>"
