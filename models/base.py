// models/base.py
"""SQLAlchemy declarative base and mixin classes."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides common columns and functionality for all models.
    """

    pass


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """Mixin providing UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Unique identifier (UUID)",
    )


class SoftDeleteMixin:
    """Mixin providing soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft-deleted",
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("FALSE"),
        doc="Flag indicating if the record is soft-deleted",
    )


def create_uuid() -> uuid.UUID:
    """Generate a new UUID4.

    Returns:
        A new UUID4 instance.
    """
    return uuid.uuid4()


# Common indexes for foreign keys and high-cardinality columns
def fk_index(table_name: str, column_name: str) -> Index:
    """Create an index for a foreign key column.

    Args:
        table_name: Name of the table.
        column_name: Name of the foreign key column.

    Returns:
        Index object for the foreign key.
    """
    return Index(
        f"ix_{table_name}_{column_name}",
        column_name,
        postgresql_using="btree",
    )


def create_timestamp_indexes(table_name: str) -> list[Index]:
    """Create standard timestamp indexes.

    Args:
        table_name: Name of the table.

    Returns:
        List of Index objects for timestamps.
    """
    return [
        Index(f"ix_{table_name}_created_at", "created_at"),
        Index(f"ix_{table_name}_updated_at", "updated_at"),
    ]
