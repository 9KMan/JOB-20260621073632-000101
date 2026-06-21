# app/models/base.py
"""Base model mixins for all database models."""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declared_attr
import uuid


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls) -> Column:
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
            index=True,
        )

    @declared_attr
    def updated_at(cls) -> Column:
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )


class UUIDMixin:
    """Mixin for UUID primary key."""

    @declared_attr
    def id(cls) -> Column:
        return Column(
            "id",
            uuid.UUID,
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )
