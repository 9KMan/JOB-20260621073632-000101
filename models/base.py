# models/base.py
"""SQLAlchemy declarative base and common mixins."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, text
from sqlalchemy.orm import Mapped, mapped_column


class BaseMixin:
    """Common mixin providing UUID primary key and timestamps."""

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        sort_order=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sort_order=99,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        sort_order=100,
    )


class TimestampMixin:
    """Mixin providing only timestamp fields (no ID)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin providing soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        server_default=text("false"),
    )


class TenantMixin:
    """Mixin providing tenant ID for multi-tenant support."""

    tenant_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def generate_uuid() -> UUID:
    """Generate a new UUID4."""
    return uuid4()


# Import Base from core.database for model declarations
# This is done at import time to ensure proper model registration
from core.database import Base

__all__ = [
    "Base",
    "BaseMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "utc_now",
    "generate_uuid",
]
