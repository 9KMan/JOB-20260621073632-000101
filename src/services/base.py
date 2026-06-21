// src/services/base.py
"""Base service class with common CRUD operations."""
from typing import Any, Generic, List, Optional, Type, TypeVar, Dict
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, joinedload

from src.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(Generic[ModelType]):
    """Base service with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize service with model class and database session."""
        self.model = model
        self.db = db

    def get(self, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        stmt = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_deleted == False  # noqa: E712
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """Get a single record by a specific field."""
        field = getattr(self.model, field_name)
        stmt = select(self.model).where(
            and_(
                field == value,
                self.model.is_deleted == False  # noqa: E712
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = True,
    ) -> tuple[List[ModelType], int]:
        """Get multiple records with pagination."""
        stmt = select(self.model).where(self.model.is_deleted == False)  # noqa: E712

        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        stmt = stmt.where(field.in_(value))
                    else:
                        stmt = stmt.where(field == value)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar()

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if desc:
                stmt = stmt.order_by(order_field.desc())
            else:
                stmt = stmt.order_by(order_field.asc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self, id: UUID, obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an existing record."""
        db_obj = self.get(id)
        if db_obj:
            for field, value in obj_in.items():
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)
            self.db.flush()
            self.db.refresh(db_obj)
        return db_obj

    def soft_delete(self, id: UUID) -> bool:
        """Soft delete a record."""
        db_obj = self.get(id)
        if db_obj:
            db_obj.soft_delete()
            self.db.flush()
            return True
        return False

    def hard_delete(self, id: UUID) -> bool:
        """Hard delete a record."""
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.flush()
            return True
        return False
