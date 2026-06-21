# models/base.py
"""SQLAlchemy declarative base for all models.

This module defines the base class that all ORM models inherit from.
It provides common columns like id, created_at, updated_at.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models.

    Provides common columns and table naming conventions.
    """

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """Mixin that adds UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Unique identifier (UUID)",
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        doc="Timestamp when the record was soft deleted",
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Soft delete flag",
    )
