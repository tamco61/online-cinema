"""Pydantic schemas for subscriptions and plans."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.db.models import PlanInterval, SubscriptionStatus


# Plan schemas
class PlanBase(BaseModel):
    """Base plan schema."""

    name: str = Field(..., max_length=100)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    interval: PlanInterval = Field(default=PlanInterval.MONTHLY)
    max_devices: int = Field(default=1, ge=1)
    supports_hd: bool = False
    supports_4k: bool = False


class PlanResponse(PlanBase):
    """Plan response schema."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Subscription schemas
class SubscriptionBase(BaseModel):
    """Base subscription schema."""

    plan_id: uuid.UUID
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscription."""

    start_date: datetime
    payment_reference: str | None = None


class SubscriptionResponse(BaseModel):
    """Subscription response schema."""

    id: uuid.UUID
    profile_id: uuid.UUID
    plan_id: uuid.UUID
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime | None
    cancelled_at: datetime | None
    auto_renew: bool
    created_at: datetime
    updated_at: datetime

    # Include plan details
    plan: PlanResponse | None = None

    model_config = {"from_attributes": True}
