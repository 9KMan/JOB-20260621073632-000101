// src/models/base.py
"""Base model classes with common functionality."""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from src.app.database import Base


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


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


class Base(UUIDMixin, TimestampMixin, Base):
    """Base class for all database models."""
    
    __abstract__ = True
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate __tablename__ from class name."""
        import re
        name = cls.__name__
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
