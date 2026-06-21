// models/base.py
"""SQLAlchemy declarative base.

All models inherit from this base class which provides:
- UUID primary key
- created_at / updated_at timestamps
- Common table arguments
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides:
    - UUID primary key with default generation
    - created_at timestamp (set on insert)
    - updated_at timestamp (set on insert and update)
    """

    __abstract__ = True
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier (UUID)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when record was last updated",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Returns:
            dict: Dictionary representation of the model
        """
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result


class TimestampMixin:
    """Mixin for adding timestamp columns to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
