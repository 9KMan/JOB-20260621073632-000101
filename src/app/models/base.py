// src/app/models/base.py
"""
Base Model Class
Provides common fields and functionality for all models.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from app.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Base model with common mixins."""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name."""
        import re
        name = cls.__name__
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class AuditableMixin(TimestampMixin):
    """Mixin for tracking who created/updated records."""
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
