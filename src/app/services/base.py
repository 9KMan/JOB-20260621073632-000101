// src/app/services/base.py
"""Base service class with common CRUD operations."""
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DuplicateException, NotFoundException
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType]):
    """Base service with common CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """Initialize the service with model and session."""
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID, load_relations: list[str] | None = None) -> ModelType:
        """Get a record by ID."""
        query = select(self.model).where(self.model.id == id)

        if load_relations:
            for relation in load_relations:
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.session.execute(query)
        record = result.scalar_one_or_none()

        if record is None:
            raise NotFoundException(self.model.__tablename__, str(id))

        return record

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        load_relations: list[str] | None = None,
    ) -> tuple[list[ModelType], int]:
        """Get all records with pagination."""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        # Get total count
        count_query = select(func.count()).select_from(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    count_query = count_query.where(getattr(self.model, key) == value)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        else:
            query = query.order_by(self.model.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Load relations if specified
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.session.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new record."""
        record = self.model(**data)
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def update(self, id: UUID, data: dict[str, Any]) -> ModelType:
        """Update an existing record."""
        record = await self.get_by_id(id)
        for key, value in data.items():
            if hasattr(record, key) and value is not None:
                setattr(record, key, value)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def delete(self, id: UUID, soft: bool = True) -> bool:
        """Delete a record (soft delete by default)."""
        record = await self.get_by_id(id)
        if soft:
            record.is_deleted = True
            record.deleted_at = func.now()
        else:
            await self.session.delete(record)
        await self.session.flush()
        return True

    async def check_unique_field(
        self,
        field: str,
        value: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """Check if a field value is unique."""
        query = select(self.model).where(getattr(self.model, field) == value)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is None
