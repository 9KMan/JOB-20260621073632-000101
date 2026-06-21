// models/base.py
"""
SQLAlchemy declarative base configuration.

This module provides the declarative base class that all ORM models inherit from.
It also includes common mixins for automatic timestamp management and UUID primary keys.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Index,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    """
    Mixin that automatically adds created_at and updated_at timestamps.
    
    Both columns use the database server time (timezone-aware UTC).
    The updated_at column is automatically updated on row modification.
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
    """
    Mixin that adds a UUID primary key with default generation.
    
    Uses PostgreSQL's gen_random_uuid() for server-side generation.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
        doc="Unique identifier (UUID v4)",
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete capability via deleted_at timestamp.
    
    Records are not physically deleted; instead, deleted_at is set.
    Active records have deleted_at = NULL.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft-deleted (NULL if active)",
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Automatically generate table name from class name."""
        return cls.__name__.lower()


def create_table_indexes(*indexes: Index) -> list[Index]:
    """
    Helper to create multiple indexes at once.
    
    Args:
        *indexes: Variable number of Index objects
        
    Returns:
        List of Index objects
    """
    return list(indexes)
