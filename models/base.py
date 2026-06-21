# models/base.py
"""SQLAlchemy declarative base and shared mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all models inherit from this."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Derive __tablename__ from the class name (snake_case)."""
        name = cls.__name__
        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result) + "s"


class UUIDMixin:
    """Adds a UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns."""

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


class SoftDeleteMixin:
    """Adds a soft-delete deleted_at column."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(
            Boolean,
            nullable=False,
            default=False,
            index=True,
        )
