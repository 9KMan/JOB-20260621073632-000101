// models/base.py
"""SQLAlchemy declarative base and mixins."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    type_annotation_map = {
        str: Text,
    }


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamp columns.

    All tables include automatic timestamp tracking for audit purposes.
    """

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


class UUIDPrimaryKey:
    """Mixin providing UUID primary key column."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )


class SoftDeleteMixin:
    """Mixin providing soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = True

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False


import uuid
