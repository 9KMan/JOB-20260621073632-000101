# models/base.py
"""SQLAlchemy declarative base."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=generate_uuid,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )


@event.listens_for(Base, "before_insert", propagate=True)
def set_created_at(mapper: Any, connection: Any, target: Any) -> None:
    """Set created_at timestamp before insert."""
    if hasattr(target, "created_at") and target.created_at is None:
        target.created_at = utc_now()


@event.listens_for(Base, "before_update", propagate=True)
def set_updated_at(mapper: Any, connection: Any, target: Any) -> None:
    """Set updated_at timestamp before update."""
    if hasattr(target, "updated_at"):
        target.updated_at = utc_now()
