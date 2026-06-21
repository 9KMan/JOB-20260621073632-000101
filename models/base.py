# models/base.py
"""SQLAlchemy declarative base and common mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides:
    - UUID primary key generation
    - Common column configurations
    - Table naming conventions
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        sort_order=0,
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name.

        Converts CamelCase to snake_case.
        Example: InvoiceLine -> invoice_line
        """
        import re

        name = cls.__name__
        # Handle special cases for pluralization
        if name.endswith("Line"):
            name = name[:-4] + "_line"
        elif name.endswith("Ref"):
            name = name[:-3] + "_ref"

        # Convert CamelCase to snake_case
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return snake + "s" if not snake.endswith("s") else snake


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps.

    All models that need automatic timestamps should inherit from this mixin.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        nullable=False,
        sort_order=99,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        sort_order=100,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality.

    Adds deleted_at column that marks records as deleted when not null.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None


def create_indexes(table_name: str, *columns: str, unique: bool = False) -> Index:
    """Create an index for the given table and columns.

    Args:
        table_name: Name of the table.
        *columns: Column names to index.
        unique: Whether the index should be unique.

    Returns:
        Index: SQLAlchemy Index object.
    """
    return Index(
        f"ix_{table_name}_{'_'.join(columns)}",
        *columns,
        unique=unique,
    )
