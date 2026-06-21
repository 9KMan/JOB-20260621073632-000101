# models/base.py
"""SQLAlchemy declarative base and common mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All database models should inherit from this class.
    Provides common table args and automatic timestamp management.
    """

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UUIDPrimaryKeyMixin:
    """Mixin to add UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    deleted_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None


def create_standard_indexes(
    table_name: str,
    columns: list[str],
) -> list[Index]:
    """Create standard indexes for high-cardinality columns.

    Args:
        table_name: Name of the table
        columns: List of column names to index

    Returns:
        list[Index]: List of Index objects
    """
    return [
        Index(f"ix_{table_name}_{column}", column)
        for column in columns
    ]


class AuditMixin:
    """Mixin to add audit trail information."""

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    modified_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )


class CompanyMixin:
    """Mixin to add company/supplier identifier for multi-tenant support."""

    company_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
