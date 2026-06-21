# models/base.py
"""SQLAlchemy declarative base configuration.

All database models should inherit from this Base class.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, String, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    Provides common table arguments and automatic timestamp management.
    """

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UUIDMixin:
    """Mixin that adds a UUID primary key."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )


@event.listens_for(Base, "before_update", propagate=True)
def set_updated_at(mapper: Any, connection: Any, target: Any) -> None:
    """Automatically update the updated_at timestamp on modifications."""
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(timezone.utc)
