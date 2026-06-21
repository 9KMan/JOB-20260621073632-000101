// src/services/base_service.py
"""
FinaRo AP Automation Core Engine
Base Service with Common Functionality
"""
import logging
from typing import Any, Generic, List, Optional, TypeVar, Type
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import BaseModel

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(Generic[ModelType]):
    """
    Base service class providing common CRUD operations.
    All other services should inherit from this class.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the service with the model class.
        
        Args:
            model: The SQLAlchemy model class
        """
        self.model = model
    
    async def get_by_id(
        self,
        db: AsyncSession,
        record_id: UUID,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get a record by its ID.
        
        Args:
            db: Database session
            record_id: The UUID of the record
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            The record or None if not found
        """
        query = select(self.model).where(self.model.id == record_id)
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of records
        """
        query = select(self.model)
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        query = query.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        db: AsyncSession,
        include_deleted: bool = False
    ) -> int:
        """
        Count total records.
        
        Args:
            db: Database session
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Total count of records
        """
        query = select(func.count(self.model.id))
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def create(
        self,
        db: AsyncSession,
        data: dict,
        commit: bool = True
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            data: Dictionary of data to create the record with
            commit: Whether to commit the transaction
            
        Returns:
            The created record
        """
        record = self.model(**data)
        db.add(record)
        
        if commit:
            await db.commit()
            await db.refresh(record)
        
        logger.info(f"Created {self.model.__name__} with id {record.id}")
        return record
    
    async def update(
        self,
        db: AsyncSession,
        record: ModelType,
        data: dict,
        commit: bool = True
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            record: The record to update
            data: Dictionary of data to update
            commit: Whether to commit the transaction
            
        Returns:
            The updated record
        """
        for key, value in data.items():
            if hasattr(record, key) and value is not None:
                setattr(record, key, value)
        
        if commit:
            await db.commit()
            await db.refresh(record)
        
        logger.info(f"Updated {self.model.__name__} with id {record.id}")
        return record
    
    async def delete(
        self,
        db: AsyncSession,
        record: ModelType,
        hard: bool = False,
        commit: bool = True
    ) -> bool:
        """
        Delete a record (soft delete by default).
        
        Args:
            db: Database session
            record: The record to delete
            hard: Whether to perform a hard delete
            commit: Whether to commit the transaction
            
        Returns:
            True if deleted successfully
        """
        if hard:
            await db.delete(record)
            logger.info(f"Hard deleted {self.model.__name__} with id {record.id}")
        else:
            record.soft_delete()
            logger.info(f"Soft deleted {self.model.__name__} with id {record.id}")
        
        if commit:
            await db.commit()
        
        return True
    
    async def search(
        self,
        db: AsyncSession,
        filters: dict,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Search for records with filters.
        
        Args:
            db: Database session
            filters: Dictionary of filter conditions
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching records
        """
        query = select(self.model).where(self.model.is_deleted == False)
        
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
