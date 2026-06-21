# models/base.py
"""SQLAlchemy declarative base and common mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Auto-generate __tablename__ from class name.
        
        Converts CamelCase to snake_case.
        Example: InvoiceLine -> invoice_line
        """
        import re
        
        name = cls.__name__
        # Handle special cases for acronyms
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier (UUID)",
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted",
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Flag indicating if record is soft deleted",
    )

    @property
    def is_active(self) -> bool:
        """Check if record is active (not deleted)."""
        return not self.is_deleted


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Base model combining common mixins.
    
    All database models should inherit from this class.
    """
    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
