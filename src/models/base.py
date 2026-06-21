# src/models/base.py
"""SQLAlchemy declarative base and mixins.

All models inherit from the Base class defined here.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All database models should inherit from this class.
    """

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps.

    Automatically manages timestamps on insert and update.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """Mixin that adds a UUID primary key.

    Uses PostgreSQL's UUID type with a server-generated default.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Unique identifier (UUID)",
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality.

    Adds a deleted_at timestamp that marks records as deleted
    instead of actually removing them from the database.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft-deleted",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None


class CreatedByMixin:
    """Mixin that tracks which user created the record."""

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User ID or identifier who created this record",
    )


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID for primary keys."""
    return uuid.uuid4()
