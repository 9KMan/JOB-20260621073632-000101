// src/models/base.py
"""Base model with common fields."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.app.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class UUIDMixin:
    """Mixin for UUID primary key."""
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model combining common mixins."""
    __abstract__ = True
