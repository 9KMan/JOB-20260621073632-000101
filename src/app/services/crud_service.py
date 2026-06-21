// src/app/services/crud_service.py
"""CRUD service for database operations."""

from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session

from src.app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDService(Generic[ModelType]):
    """Generic CRUD service for database models."""

    def __init__(self, model: Type[ModelType]):
        """Initialize with model class."""
        self.model = model

    def get(self, db: Session, id: str) -> Optional[ModelType]:
        """Get single record by ID."""
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False  # noqa: E712
        ).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        query = db.query(self.model).filter(self.model.is_deleted == False)  # noqa: E712
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()

    def get_count(self, db: Session, filters: Optional[dict] = None) -> int:
        """Get total count of records."""
        query = db.query(self.model).filter(self.model.is_deleted == False)  # noqa: E712
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()

    def create(self, db: Session, obj_in: dict) -> ModelType:
        """Create new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, id: str, obj_in: dict) -> Optional[ModelType]:
        """Update existing record."""
        db_obj = self.get(db, id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key) and value is not None:
                    setattr(db_obj, key, value)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: str) -> bool:
        """Soft delete a record."""
        db_obj = self.get(db, id)
        if db_obj:
            db_obj.soft_delete()
            db.commit()
            return True
        return False

    def exists(self, db: Session, id: str) -> bool:
        """Check if record exists."""
        return self.get(db, id) is not None
