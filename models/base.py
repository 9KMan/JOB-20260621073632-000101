# models/base.py
"""
SQLAlchemy declarative base and mixins.

Provides the base class for all models and common mixins.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    
    All tables should include these columns for audit purposes.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """
    Mixin that adds a UUID primary key.
    
    Uses UUIDs instead of auto-increment integers for better distribution
    and security.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier (UUID)",
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality.
    
    Records are not physically deleted but marked with deleted_at timestamp.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


class TenantMixin:
    """
    Mixin that adds tenant_id for multi-tenancy support.
    
    Currently out of scope but provided for future extension.
    """

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
        doc="Tenant identifier for multi-tenancy",
    )
