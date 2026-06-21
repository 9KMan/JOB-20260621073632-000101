# models/base.py
"""
SQLAlchemy declarative base configuration.

Defines the base class for all models with common columns
and configuration.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides:
    - UUID primary key with auto-generation
    - created_at timestamp (set on insert)
    - updated_at timestamp (set on insert and update)
    - Soft delete support via deleted_at
    """

    __abstract__ = True

    # UUID primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        index=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the model.
        """
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None


class TimestampMixin:
    """
    Mixin for models that need timestamps.
    
    Provides created_at and updated_at columns.
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


class UUIDPrimaryKeyMixin:
    """
    Mixin for models that need UUID primary keys.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin for models that support soft deletion.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.updated_at = datetime.now(timezone.utc)

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None
