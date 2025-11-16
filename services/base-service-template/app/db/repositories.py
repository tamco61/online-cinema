"""
Repository pattern for database operations.

Repositories encapsulate database queries and provide a clean interface
for data access.
"""

from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    This class provides basic database operations that can be inherited
    by specific repositories.

    Example:
        ```python
        from app.db.models import ExampleModel
        from app.db.repositories import BaseRepository

        class ExampleRepository(BaseRepository[ExampleModel]):
            pass

        # Usage
        repo = ExampleRepository(db, ExampleModel)
        item = await repo.get_by_id(1)
        ```
    """

    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        """
        Initialize repository.

        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(
        self,
        id: int,
        **kwargs: Any,
    ) -> Optional[ModelType]:
        """
        Update a record by ID.

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(id)

        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)

        if instance is None:
            return False

        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def exists(self, id: int) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        result = await self.db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
