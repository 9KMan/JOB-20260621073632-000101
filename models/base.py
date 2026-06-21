// models/base.py
"""SQLAlchemy declarative base configuration."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }

    @classmethod
    def generate_uuid(cls) -> str:
        """Generate a UUID4 string."""
        return str(uuid4())


class TimestampMixin:
    """Mixin for created_at and updated_at timestamp columns."""

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
    """Mixin for UUID primary key."""

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=UUIDMixin.generate_uuid,
        doc="UUID primary key",
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by: Mapped[str | None] = mapped_column(
        nullable=True,
        doc="ID of user who soft deleted the record",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None


def create_indexes(
    table_name: str,
    columns: list[str],
    unique: bool = False,
    name: str | None = None,
) -> Index:
    """
    Create an index for the specified columns.

    Args:
        table_name: Name of the table
        columns: List of column names
        unique: Whether the index is unique
        name: Optional custom index name

    Returns:
        Index object
    """
    idx_name = name or f"ix_{table_name}_{'_'.join(columns)}"
    return Index(
        idx_name,
        *columns,
        unique=unique,
        if_not_exists=True,
    )
