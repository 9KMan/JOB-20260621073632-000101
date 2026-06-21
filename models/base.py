# models/base.py
"""SQLAlchemy declarative base configuration."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides:
    - UUID primary key generation
    - Automatic created_at/updated_at timestamps
    - Soft delete support via deleted_at
    """

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete support."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary key generation."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )


class TimestampTriggerMixin:
    """Mixin that adds database triggers for updated_at (PostgreSQL)."""

    pass


# Event listener to set updated_at before update
@event.listens_for(TimestampMixin, "before_update", propagate=True)
def set_updated_at(mapper: Any, connection: Any, target: Any) -> None:
    """Automatically set updated_at before any update operation."""
    target.updated_at = datetime.now(timezone.utc)


__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDPrimaryKeyMixin",
    "TimestampTriggerMixin",
]
