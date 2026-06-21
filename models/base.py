# models/base.py
"""SQLAlchemy declarative base configuration.

All models inherit from this base class which provides
common columns like id, created_at, and updated_at.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, convention


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps.

    All tables include automatic timestamp tracking.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin providing UUID primary key.

    Uses PostgreSQL UUID type with server-generated values.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin providing soft delete functionality.

    Adds deleted_at timestamp for soft deletes.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "utc_now",
]
