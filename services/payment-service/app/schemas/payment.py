from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentStatusEnum(str, Enum):
    """Payment status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentProviderEnum(str, Enum):
    """Payment provider enum"""
    YOOMONEY = "yoomoney"
    STRIPE = "stripe"
    PAYPAL = "paypal"


# Request Schemas

class CreateCheckoutSessionRequest(BaseModel):
    """Request to create checkout session"""
    plan_id: str = Field(..., description="Subscription plan ID (basic, premium, family)")
    user_id: UUID4 = Field(..., description="User UUID")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate prevention")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "premium",
                "user_id": "00000000-0000-0000-0000-000000000001",
                "idempotency_key": "unique-key-123"
            }
        }


class YooMoneyWebhookEvent(BaseModel):
    """YooMoney webhook event"""
    type: str = Field(..., description="Event type (payment.succeeded, payment.canceled, refund.succeeded)")
    event: str = Field(..., description="Event name")
    object: dict = Field(..., description="Payment object")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {
                    "id": "2d8b8b7a-000f-5000-9000-1b7e3f9e0e9f",
                    "status": "succeeded",
                    "amount": {"value": "599.00", "currency": "RUB"},
                    "metadata": {"payment_id": "uuid"}
                }
            }
        }


# Response Schemas

class CheckoutSessionResponse(BaseModel):
    """Response with checkout session details"""
    payment_id: UUID4
    checkout_url: str
    amount: float
    currency: str
    plan_id: str
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "payment_id": "00000000-0000-0000-0000-000000000001",
                "checkout_url": "https://yoomoney.ru/checkout/...",
                "amount": 599.00,
                "currency": "RUB",
                "plan_id": "premium",
                "expires_at": "2024-11-16T12:00:00Z"
            }
        }


class PaymentResponse(BaseModel):
    """Payment response"""
    id: UUID4
    user_id: UUID4
    amount: float
    currency: str
    status: PaymentStatusEnum
    provider: PaymentProviderEnum
    provider_payment_id: Optional[str] = None
    plan_id: Optional[str] = None
    subscription_duration_days: Optional[int] = None
    checkout_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "00000000-0000-0000-0000-000000000001",
                "user_id": "00000000-0000-0000-0000-000000000002",
                "amount": 599.00,
                "currency": "RUB",
                "status": "succeeded",
                "provider": "yoomoney",
                "provider_payment_id": "2d8b8b7a-000f-5000-9000-1b7e3f9e0e9f",
                "plan_id": "premium",
                "subscription_duration_days": 30,
                "checkout_url": "https://yoomoney.ru/checkout/...",
                "created_at": "2024-11-16T10:00:00Z",
                "updated_at": "2024-11-16T10:05:00Z",
                "completed_at": "2024-11-16T10:05:00Z"
            }
        }


class PaymentHistoryResponse(BaseModel):
    """Payment history response"""
    payments: list[PaymentResponse]
    total: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "payments": [],
                "total": 10,
                "page": 1,
                "page_size": 20
            }
        }


class WebhookResponse(BaseModel):
    """Webhook processing response"""
    success: bool
    message: str
    payment_id: Optional[UUID4] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Payment processed successfully",
                "payment_id": "00000000-0000-0000-0000-000000000001"
            }
        }


# Internal Schemas

class UpdateSubscriptionRequest(BaseModel):
    """Request to update user subscription in user-service"""
    user_id: UUID4
    plan_id: str
    duration_days: int
    payment_id: UUID4

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "plan_id": "premium",
                "duration_days": 30,
                "payment_id": "00000000-0000-0000-0000-000000000002"
            }
        }
