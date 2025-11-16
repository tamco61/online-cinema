"""
Database models for User Service.

Models:
- UserProfile: User profile information
- Plan: Subscription plans (pricing tiers)
- Subscription: User subscriptions to plans
- WatchHistory: User watch history with progress
- Favorite: User favorite content
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class PlanInterval(str, enum.Enum):
    """Subscription plan billing interval."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class UserProfile(Base):
    """
    User profile model.

    Stores additional user information beyond authentication.
    user_id references User.id from auth-service.
    """

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key to auth-service User (we don't have FK constraint across services)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        comment="References users.id from auth-service",
    )

    # Profile information
    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
        comment="ISO 639-1 language code",
    )

    country: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        comment="ISO 3166-1 alpha-2 country code",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    watch_history: Mapped[list["WatchHistory"]] = relationship(
        "WatchHistory",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, user_id={self.user_id}, nickname='{self.nickname}')>"


class Plan(Base):
    """
    Subscription plan model.

    Defines available subscription tiers and pricing.
    """

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Pricing
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="ISO 4217 currency code",
    )

    interval: Mapped[PlanInterval] = mapped_column(
        Enum(PlanInterval),
        default=PlanInterval.MONTHLY,
        nullable=False,
    )

    # Features (JSON or specific columns)
    max_devices: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    supports_hd: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    supports_4k: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="plan",
    )

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, name='{self.name}', price={self.price})>"


class Subscription(Base):
    """
    User subscription model.

    Tracks user subscriptions to plans.
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False,
        index=True,
    )

    # Subscription details
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus),
        default=SubscriptionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Dates
    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    end_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Payment reference (could be Stripe subscription ID, etc.)
    payment_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Auto-renewal
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="subscriptions",
    )

    plan: Mapped["Plan"] = relationship(
        "Plan",
        back_populates="subscriptions",
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, profile_id={self.profile_id}, status={self.status})>"


class WatchHistory(Base):
    """
    User watch history model.

    Tracks what content users have watched and their progress.
    """

    __tablename__ = "watch_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content reference (from content-service)
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="References content from content-service",
    )

    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type: movie, episode, etc.",
    )

    # Watch progress
    progress_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Watch progress in seconds",
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total content duration in seconds",
    )

    # Completed flag
    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Last watched time
    last_watched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="watch_history",
    )

    def __repr__(self) -> str:
        return f"<WatchHistory(id={self.id}, content_id={self.content_id}, progress={self.progress_seconds}s)>"


class Favorite(Base):
    """
    User favorites model.

    Stores user's favorite/bookmarked content.
    """

    __tablename__ = "favorites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content reference (from content-service)
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="References content from content-service",
    )

    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type: movie, series, etc.",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="favorites",
    )

    def __repr__(self) -> str:
        return f"<Favorite(id={self.id}, content_id={self.content_id})>"

    class Config:
        # Unique constraint: one user can favorite content only once
        __table_args__ = (
            # UniqueConstraint('profile_id', 'content_id', name='uq_profile_content'),
        )
