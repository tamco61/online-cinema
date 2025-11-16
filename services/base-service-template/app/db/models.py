"""
SQLAlchemy database models.

This module contains all database models for the service.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .session import Base


class BaseModel(Base):
    """
    Base model with common fields.

    All models should inherit from this class.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
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

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Example model - remove or modify for specific service
class ExampleModel(BaseModel):
    """
    Example model.

    Replace this with actual models for your service.
    """

    __tablename__ = "examples"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ExampleModel(id={self.id}, name='{self.name}')>"
