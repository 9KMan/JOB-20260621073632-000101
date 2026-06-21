# models/base.py
# SQLAlchemy declarative base and mixins
# AP Automation Core Engine — FinaRo

"""SQLAlchemy declarative base and common mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All ORM models should inherit from this class.
    Provides type-safe column definitions and common functionality.
    """

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns.

    Automatically maintains timestamps on insert and update operations.
    Uses UTC timezone for all timestamps.

    Attributes:
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

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
    """Mixin that adds a UUID primary key column.

    Uses PostgreSQL's UUID type with a randomly generated default value.

    Attributes:
        id: UUID primary key.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID primary key",
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality.

    Adds a deleted_at timestamp column that is NULL for active records
    and set to the deletion timestamp for deleted records.

    Attributes:
        deleted_at: Timestamp when the record was soft deleted, or NULL if active.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted",
    )


def generate_uuid() -> uuid.UUID:
    """Generate a new random UUID.

    Returns:
        uuid.UUID: A new randomly generated UUID.
    """
    return uuid.uuid4()
