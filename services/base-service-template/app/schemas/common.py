"""
Common Pydantic schemas used across the service.
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class BaseSchema(BaseModel):
    """
    Base Pydantic schema with common configuration.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class MessageResponse(BaseSchema):
    """
    Simple message response.

    Example:
        ```python
        @app.post("/action")
        async def action():
            return MessageResponse(message="Action completed successfully")
        ```
    """

    message: str = Field(..., description="Response message")


class HealthResponse(BaseSchema):
    """
    Health check response.

    Example:
        ```python
        @app.get("/health")
        async def health():
            return HealthResponse(
                status="healthy",
                service="catalog-service",
                version="1.0.0"
            )
        ```
    """

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    details: Optional[dict[str, Any]] = Field(None, description="Additional health details")


class PaginationParams(BaseSchema):
    """
    Pagination parameters.

    Example:
        ```python
        from fastapi import Depends

        @app.get("/items")
        async def list_items(pagination: PaginationParams = Depends()):
            # Use pagination.skip and pagination.limit
            return items[pagination.skip:pagination.skip + pagination.limit]
        ```
    """

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """
    Paginated response wrapper.

    Example:
        ```python
        @app.get("/items")
        async def list_items():
            return PaginatedResponse(
                items=items,
                total=len(items),
                skip=0,
                limit=100
            )
        ```
    """

    items: list[DataT] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of skipped items")
    limit: int = Field(..., description="Page size")

    @property
    def has_more(self) -> bool:
        """Check if there are more items available."""
        return self.skip + self.limit < self.total


class TimestampMixin(BaseSchema):
    """
    Mixin for models with timestamps.

    Example:
        ```python
        class MovieSchema(TimestampMixin):
            id: int
            title: str
        ```
    """

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class IDMixin(BaseSchema):
    """
    Mixin for models with ID.
    """

    id: int = Field(..., description="Record ID", gt=0)


# Example schema - remove or modify for specific service
class ExampleBase(BaseSchema):
    """Base example schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Name")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    is_active: bool = Field(default=True, description="Active status")


class ExampleCreate(ExampleBase):
    """Schema for creating an example."""

    pass


class ExampleUpdate(BaseSchema):
    """Schema for updating an example."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class ExampleResponse(ExampleBase, IDMixin, TimestampMixin):
    """Schema for example response."""

    pass
