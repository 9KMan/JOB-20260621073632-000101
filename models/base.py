// models/base.py
"""SQLAlchemy declarative base for all database models.

This module defines the base class for all SQLAlchemy models in the application.
It provides common columns (UUID primary keys, timestamps) and configuration
for the ORM.

All models inherit from this base and must use UUID primary keys
as specified in the project requirements.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.
    
    Provides:
    - UUID primary key generation
    - Automatic created_at/updated_at timestamps
    - Common configuration for all models
    
    Attributes:
        id: UUID primary key with auto-generation
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
    """

    # Use PostgreSQL UUID type
    __table_args__ = {
        "schema": None,  # Default schema (public)
    }

    # Common columns for all models
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier (UUID v4)",
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last modified",
    )

    def __repr__(self) -> str:
        """Generate string representation of model instance."""
        return f"<{self.__class__.__name__} id={self.id}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.
        
        Returns a dictionary representation with UUID values
        converted to strings for JSON serialization.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result


class TimestampMixin:
    """Mixin for adding timestamp columns to models.
    
    Use this mixin for models that need custom timestamp handling
    or don't inherit directly from Base.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin for adding UUID primary key to models."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class SoftDeleteMixin:
    """Mixin for adding soft delete capability to models.
    
    Adds a deleted_at column that marks records as deleted
    without actually removing them from the database.
    """
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when record was soft deleted",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None
