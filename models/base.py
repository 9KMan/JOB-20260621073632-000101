# models/base.py
"""SQLAlchemy declarative base and shared mixins."""

import uuid
from datetime import datetime, timezone
from typing import ClassVar

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at / updated_at timestamp columns."""

    __abstract__: ClassVar[bool] = True

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
    """Mixin that adds a UUID primary key."""

    __abstract__: ClassVar[bool] = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
