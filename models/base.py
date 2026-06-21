# models/base.py
"""SQLAlchemy declarative base and mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda ctx: datetime.now(timezone.utc),
        doc="Timestamp when the record was last updated",
    )


class UUIDPrimaryKeyMixin:
    """Mixin to add UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier (UUID)",
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted",
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Whether the record is soft deleted",
    )

    def soft_delete(self) -> None:
        """Mark the record as soft deleted."""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_deleted = True


def create_indexes(base: type[Base]) -> list[Index]:
    """Create standard indexes for high-cardinality columns.

    Args:
        base: SQLAlchemy declarative base class

    Returns:
        List of Index objects
    """
    return [
        Index("ix_common_created_at", "created_at"),
        Index("ix_common_updated_at", "updated_at"),
    ]
