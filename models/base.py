// models/base.py
"""SQLAlchemy declarative base and mixins."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class Base:
    """Base class for all database models.

    Provides common columns and functionality:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        type_=String(36),
        sortable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        sortable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=utc_now,
        sortable=True,
    )


class TimestampMixin:
    """Mixin for adding timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=utc_now,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.is_deleted = True
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Restore deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class TenantMixin:
    """Mixin for multi-tenant support."""

    tenant_id: Mapped[UUID] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
