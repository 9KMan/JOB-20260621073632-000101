// src/models/base.py
"""Base models with common mixins."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class BaseModel(UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Base model with all common mixins."""
    
    __abstract__ = True
