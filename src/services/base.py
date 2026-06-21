// src/services/base.py
"""Base service class with common functionality."""
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from src.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
SchemaType = TypeVar("SchemaType")


class BaseService(Generic[ModelType]):
    """Base service with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize service with model and database session."""
        self.model = model
        self.db = db

    def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities with pagination."""
        return (
            self.db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, data: Any) -> ModelType:
        """Create a new entity."""
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, id: str, data: Any) -> Optional[ModelType]:
        """Update an existing entity."""
        entity = self.get_by_id(id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.db.commit()
            self.db.refresh(entity)
        return entity

    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """Count total entities."""
        return self.db.query(self.model).count()

    def exists(self, id: str) -> bool:
        """Check if entity exists."""
        return self.db.query(self.model).filter(self.model.id == id).count() > 0
