// src/app/models/base.py
"""
Base model classes and mixins.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UUIDPrimaryKey:
    """Mixin for UUID primary key."""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted = Column(
        text("boolean").default("false"),
        nullable=False,
        server_default=text("false"),
    )
