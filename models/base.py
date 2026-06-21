# models/base.py
"""SQLAlchemy declarative base and mixin classes.

Provides the base class for all models and reusable mixins.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All database models inherit from this class.
    """

    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

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


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )


class TenantMixin:
    """Mixin for multi-tenant support (if needed in future)."""

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )


def create_uuid() -> uuid.UUID:
    """Generate a new UUID4.

    Returns:
        uuid.UUID: New UUID4
    """
    return uuid.uuid4()


def utc_now() -> datetime:
    """Get current UTC datetime.

    Returns:
        datetime: Current UTC datetime
    """
    return datetime.now(timezone.utc)
