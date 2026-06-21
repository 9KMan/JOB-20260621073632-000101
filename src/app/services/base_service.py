// src/app/services/base_service.py
"""
Base service class for common CRUD operations.
"""
from typing import TypeVar, Generic, Type, List, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """Base service with common CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by(
        self, field_name: str, value: Any, load_relations: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Get a single record by a field."""
        query = select(self.model).where(getattr(self.model, field_name) == value)
        if load_relations:
            for relation in load_relations:
                query = query.options(selectinload(getattr(self.model, relation)))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        load_relations: Optional[List[str]] = None,
        filters: Optional[dict] = None,
    ) -> List[ModelType]:
        """Get all records with pagination."""
        query = select(self.model)
        if filters:
            for field, value in filters.items():
                query = query.where(getattr(self.model, field) == value)
        if load_relations:
            for relation in load_relations:
                query = query.options(selectinload(getattr(self.model, relation)))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[dict] = None) -> int:
        """Count records."""
        query = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, obj_in: dict) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: UUID, obj_in: dict) -> Optional[ModelType]:
        """Update a record."""
        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**obj_in)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        """Delete a record."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def soft_delete(self, id: UUID) -> bool:
        """Soft delete a record."""
        from datetime import datetime
        result = await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(is_deleted=True, deleted_at=datetime.utcnow())
        )
        await self.session.flush()
        return result.rowcount > 0
