"""
Base service class for business logic.

Services encapsulate business logic and orchestrate operations
between repositories, external APIs, and other services.
"""

from typing import Generic, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import BaseRepository
from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class with common business logic operations.

    This class provides a layer between API endpoints and repositories,
    where you can implement complex business logic, validation, and
    orchestration.

    Example:
        ```python
        from app.db.models import ExampleModel
        from app.schemas.common import ExampleCreate, ExampleUpdate
        from app.services.base_service import BaseService

        class ExampleService(BaseService[ExampleModel, ExampleCreate, ExampleUpdate]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, ExampleModel)

            async def custom_logic(self, id: int) -> ExampleModel:
                # Implement custom business logic here
                item = await self.repository.get_by_id(id)
                # ... more logic
                return item
        ```
    """

    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        """
        Initialize service.

        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
        self.repository = BaseRepository[ModelType](db, model)

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get an item by ID.

        Args:
            id: Item ID

        Returns:
            Model instance or None if not found
        """
        return await self.repository.get_by_id(id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """
        Get all items with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of model instances
        """
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new item.

        Args:
            obj_in: Creation schema

        Returns:
            Created model instance
        """
        # Convert Pydantic model to dict
        obj_data = obj_in.model_dump()

        # Create using repository
        return await self.repository.create(**obj_data)

    async def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
    ) -> Optional[ModelType]:
        """
        Update an item.

        Args:
            id: Item ID
            obj_in: Update schema

        Returns:
            Updated model instance or None if not found
        """
        # Convert Pydantic model to dict, excluding unset fields
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Update using repository
        return await self.repository.update(id, **obj_data)

    async def delete(self, id: int) -> bool:
        """
        Delete an item.

        Args:
            id: Item ID

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(id)

    async def exists(self, id: int) -> bool:
        """
        Check if an item exists.

        Args:
            id: Item ID

        Returns:
            True if exists, False otherwise
        """
        return await self.repository.exists(id)
