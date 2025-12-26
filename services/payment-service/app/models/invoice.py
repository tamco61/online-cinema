from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status enum"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Invoice(Base):
    """
    Invoice model

    Optional: Invoice generation for payments
    Can be used for accounting, reporting, and user receipts
    """
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)

    # Relations
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True, index=True)

    # Invoice details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)

    # Billing details
    description = Column(Text, nullable=True)
    plan_id = Column(String(50), nullable=True)

    # Dates
    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=True)
    paid_date = Column(DateTime, nullable=True)

    # Metadata
    invoice_metadata = Column(Text, nullable=True)  # JSON string

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, amount={self.amount}, status={self.status})>"

    def generate_invoice_number(self) -> str:
        """
        Generate unique invoice number

        Format: INV-YYYYMMDD-XXXXX
        Example: INV-20241116-00001
        """
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y%m%d")
        # In production, you'd query DB for the last invoice of the day
        # For now, using UUID suffix
        suffix = str(uuid.uuid4())[:5].upper()
        return f"INV-{date_str}-{suffix}"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "user_id": str(self.user_id),
            "payment_id": str(self.payment_id) if self.payment_id else None,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "description": self.description,
            "plan_id": self.plan_id,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
