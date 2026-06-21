# models/base.py
"""
SQLAlchemy declarative base.

All models inherit from this base. Provides UUID primary key,
timestamps, and common column definitions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Self

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all models.
    
    Provides:
    - UUID primary key (not auto-increment)
    - created_at / updated_at timestamps
    - Automatic table naming from class name
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        sortable=True,
        comment="Unique identifier (UUID v4)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        sortable=True,
        comment="Record creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        sortable=True,
        comment="Last update timestamp",
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Automatic table name generation from class name.
        
        Converts CamelCase to snake_case.
        E.g., InvoiceLine -> invoice_line
        """
        import re
        name = cls.__name__
        # Insert underscore before uppercase letters and lowercase the result
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return snake

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"

    @classmethod
    def get_by_id(cls, session, model_id: uuid.UUID) -> Self | None:
        """Get model instance by ID."""
        return session.get(cls, model_id)

    @classmethod
    async def get_by_id_async(cls, session, model_id: uuid.UUID) -> Self | None:
        """Get model instance by ID (async)."""
        return await session.get(cls, model_id)


class SoftDeleteMixin:
    """Mixin for soft-delete pattern (deleted_at timestamp)."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Soft delete timestamp (NULL = active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        from datetime import datetime, timezone
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
