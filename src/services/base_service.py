// src/services/base_service.py
"""Base service class with common CRUD operations."""
from typing import TypeVar, Generic, Type, Optional, List, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class providing common CRUD operations.
    
    Type Parameters:
        ModelType: The SQLAlchemy model class
        CreateSchemaType: The Pydantic schema for creating records
        UpdateSchemaType: The Pydantic schema for updating records
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize the service.
        
        Args:
            model: The SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: The record UUID
            
        Returns:
            The record or None if not found
        """
        return self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False  # noqa: E712
        ).first()
    
    def get_by(self, **kwargs) -> Optional[ModelType]:
        """
        Get a single record by arbitrary filters.
        
        Args:
            **kwargs: Filter conditions
            
        Returns:
            The record or None if not found
        """
        query = self.db.query(self.model).filter(self.model.is_deleted == False)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **kwargs
    ) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **kwargs: Additional filter conditions
            
        Returns:
            List of records
        """
        query = self.db.query(self.model).filter(self.model.is_deleted == False)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.offset(skip).limit(limit).all()
    
    def create(self, schema: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            schema: The create schema
            
        Returns:
            The created record
        """
        data = schema.model_dump() if hasattr(schema, 'model_dump') else schema.dict()
        db_obj = self.model(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        id: UUID,
        schema: UpdateSchemaType
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: The record UUID
            schema: The update schema
            
        Returns:
            The updated record or None if not found
        """
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        update_data = schema.model_dump(exclude_unset=True) if hasattr(schema, 'model_dump') else schema.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: UUID, soft: bool = True) -> bool:
        """
        Delete a record.
        
        Args:
            id: The record UUID
            soft: If True, perform soft delete; otherwise hard delete
            
        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        if soft:
            from datetime import datetime, timezone
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now(timezone.utc)
            self.db.commit()
        else:
            self.db.delete(db_obj)
            self.db.commit()
        
        return True
    
    def count(self, **kwargs) -> int:
        """
        Count records matching filters.
        
        Args:
            **kwargs: Filter conditions
            
        Returns:
            Count of matching records
        """
        query = self.db.query(self.model).filter(self.model.is_deleted == False)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.count()
