from sqlalchemy import Column, String, Float, DateTime, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentProvider(str, enum.Enum):
    """Payment provider enum"""
    YOOMONEY = "yoomoney"
    STRIPE = "stripe"
    PAYPAL = "paypal"


class Payment(Base):
    """
    Payment model

    Stores all payment transactions
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)

    # Provider details
    provider = Column(Enum(PaymentProvider), nullable=False, default=PaymentProvider.YOOMONEY)
    provider_payment_id = Column(String(255), nullable=True, unique=True, index=True)

    # Subscription details
    plan_id = Column(String(50), nullable=True)
    subscription_duration_days = Column(Integer, nullable=True)

    # Idempotency
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)

    # Metadata
    metadata = Column(Text, nullable=True)  # JSON string for additional data

    # Checkout session
    checkout_url = Column(String(512), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "provider": self.provider.value,
            "provider_payment_id": self.provider_payment_id,
            "plan_id": self.plan_id,
            "subscription_duration_days": self.subscription_duration_days,
            "checkout_url": self.checkout_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
