# models/base.py
"""SQLAlchemy declarative base and shared mixins.

Provides the base class for all models and common mixins for
UUID primary keys and timestamp fields.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models should inherit from this class.
    """

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class UUIDMixin:
    """Mixin providing UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps.

    Both fields are automatically managed by SQLAlchemy.
    """

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


class SoftDeleteMixin:
    """Mixin providing soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_deleted = True

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False


class TableNameMixin:
    """Mixin providing automatic table name generation."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name.

        Converts CamelCase to snake_case.
        Example: PurchaseOrder -> purchase_order
        """
        import re

        name = cls.__name__
        # Insert underscore before uppercase letters and lowercase the result
        table_name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return table_name


class DictableMixin:
    """Mixin providing dictionary conversion methods."""

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            dict[str, Any]: Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result

    def to_dict_safe(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary, excluding specified fields.

        Args:
            exclude: List of field names to exclude

        Returns:
            dict[str, Any]: Dictionary representation
        """
        exclude = exclude or []
        result = self.to_dict()
        for field in exclude:
            result.pop(field, None)
        return result
