// src/app/services/base.py
"""
Base Service Class
Provides common CRUD operations for all services.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import BaseModel
from app.core.database import get_db_context

T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T]):
    """Base service with common CRUD operations."""
    
    def __init__(self, model: Type[T], session: Optional[AsyncSession] = None):
        self.model = model
        self._session = session
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self._session:
            return self._session
        async with get_db_context() as session:
            return session
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        session = await self._get_session()
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """Get all entities with pagination and filters."""
        session = await self._get_session()
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        if order_by:
            if order_by.startswith("-"):
                attr = getattr(self.model, order_by[1:], None)
                if attr:
                    query = query.order_by(attr.desc())
            else:
                attr = getattr(self.model, order_by, None)
                if attr:
                    query = query.order_by(attr)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[dict] = None) -> int:
        """Count entities."""
        session = await self._get_session()
        query = select(func.count(self.model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await session.execute(query)
        return result.scalar_one()
    
    async def create(self, data: dict) -> T:
        """Create new entity."""
        session = await self._get_session()
        entity = self.model(**data)
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return entity
    
    async def update(self, id: UUID, data: dict) -> Optional[T]:
        """Update entity."""
        session = await self._get_session()
        
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return await self.get_by_id(id)
        
        await session.execute(
            update(self.model).where(self.model.id == id).values(**update_data)
        )
        await session.flush()
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID, soft: bool = True) -> bool:
        """Delete entity (soft delete by default)."""
        session = await self._get_session()
        
        if soft and hasattr(self.model, "is_deleted"):
            await session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(is_deleted=True)
            )
        else:
            await session.execute(
                delete(self.model).where(self.model.id == id)
            )
        
        await session.flush()
        return True
    
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        session = await self._get_session()
        result = await session.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return result.scalar_one() > 0
