// models/base.py
"""SQLAlchemy declarative base for all models.

This module defines the Base class that all models inherit from.
It includes common columns and mixins for all database tables.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.
    
    Provides:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    - is_deleted soft-delete flag
    """

    __abstract__ = True

    # Primary key - UUID v4
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False,
        sortable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sortable=True,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        sortable=True,
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def soft_delete(self) -> None:
        """Mark record as deleted (soft delete)."""
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.is_deleted = False
        self.updated_at = datetime.now(timezone.utc)


def generate_uuid() -> UUID:
    """Generate a new UUID v4.

    Returns:
        UUID: A new unique identifier.
    """
    return uuid4()


# ============================================
# Common Indexes
# ============================================

def create_indexes(*index_names: str) -> list[Index]:
    """Create standard indexes for common query patterns.

    Args:
        *index_names: Names of indexes to create.

    Returns:
        list[Index]: List of Index objects.
    """
    indexes = []
    
    for name in index_names:
        if name == "status":
            indexes.append(Index("ix_common_status", "status"))
        elif name == "created_at":
            indexes.append(Index("ix_common_created_at", "created_at"))
        elif name == "external_id":
            indexes.append(Index("ix_common_external_id", "external_id"))
    
    return indexes


# ============================================
# SQLAlchemy Event Listeners
# ============================================

def setup_event_listeners():
    """Setup SQLAlchemy event listeners for common operations."""
    from sqlalchemy import event
    
    @event.listens_for(Base, "before_insert", propagate=True)
    def set_created_at(mapper, connection, target):
        """Set created_at timestamp before insert."""
        if hasattr(target, "created_at") and target.created_at is None:
            target.created_at = datetime.now(timezone.utc)
    
    @event.listens_for(Base, "before_update", propagate=True)
    def set_updated_at(mapper, connection, target):
        """Set updated_at timestamp before update."""
        if hasattr(target, "updated_at"):
            target.updated_at = datetime.now(timezone.utc)
