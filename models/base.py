// models/base.py
"""Base model classes with common mixins."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr

from core.database import Base


class UUIDMixin:
    """Mixin that adds UUID primary key."""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    @declared_attr
    def is_deleted(cls):
        return Column(DateTime(timezone=True), nullable=True, default=None)


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Abstract base model with common fields."""
    
    __abstract__ = True
    
    @classmethod
    def get_by_id(cls, db, model_id: uuid.UUID):
        """Get a single record by ID."""
        return db.query(cls).filter(cls.id == model_id).first()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
