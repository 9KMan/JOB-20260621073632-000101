// models/base.py
"""SQLAlchemy declarative base.

All database models inherit from this Base class.
Provides common columns and table configurations.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    - Soft delete support
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        sort_order=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        sort_order=1,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        sort_order=2,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        sort_order=3,
    )

    def soft_delete(self) -> None:
        """Mark record as deleted (soft delete pattern)."""
        self.deleted_at = datetime.now(timezone.utc)

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None


def created_at_default() -> datetime:
    """Factory for created_at default timestamp."""
    return datetime.now(timezone.utc)


def updated_at_default() -> datetime:
    """Factory for updated_at default timestamp."""
    return datetime.now(timezone.utc)
