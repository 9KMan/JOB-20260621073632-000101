// src/models/base.py
"""Base model classes with common functionality."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Boolean, func
from sqlalchemy.orm import declared_attr, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality."""
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Abstract base model with UUID primary key and common mixins.
    
    All database models should inherit from this class.
    """
    
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True
    )
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        
        Converts CamelCase to snake_case.
        Example: PurchaseOrder -> purchase_orders
        """
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower() + "s"
