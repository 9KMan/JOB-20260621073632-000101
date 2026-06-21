# models/base.py
"""SQLAlchemy base configuration and mixins.

Provides the declarative base class and common mixins for all models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models.

    All database models should inherit from this class.
    """

    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps.

    Automatically manages timestamps on record creation and update.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UUIDMixin:
    """Mixin for UUID primary key.

    Provides a UUID v4 primary key with automatic generation.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality.

    Provides a deleted_at column for soft delete support.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None


def generate_uuid() -> uuid.UUID:
    """Generate a UUID v4.

    Returns:
        New UUID v4 instance
    """
    return uuid.uuid4()


# Standard indexes for common queries
BASE_INDEXES = [
    Index("ix_created_at", "created_at"),
    Index("ix_updated_at", "updated_at"),
]
