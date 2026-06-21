# models/base.py
"""SQLAlchemy declarative base and mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class UUIDPrimaryKey:
    """
    Mixin that adds a UUID primary-key column called `id`.

    Uses server-generated UUID v4 by default.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        sort_key=lambda: uuid.uuid4(),  # allows ORDER BY id in SQLite compat mode
    )


class Timestamps:
    """
    Mixin that adds `created_at` and `updated_at` datetime columns.

    - ``created_at`` is set once on insert.
    - ``updated_at`` is refreshed on every insert and update via ``onupdate``.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=Func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=Func.now(),
        onupdate=lambda _: datetime.now(timezone=True),
    )


class AuditMixin:
    """
    Mixin that adds an `audit_json` column for storing mutable audit metadata.

    Use cases: store who triggered a status change, raw ERP payload snippets, etc.
    """

    audit_json: Mapped[dict[str, Any] | None] = mapped_column(
        default=None,
        nullable=True,
    )


# ── Common indexes ─────────────────────────────────────────────────────────────

def _fk_index(table_name: str, column_name: str) -> Index:
    """Return an Index for a foreign-key column."""
    return Index(f"ix_{table_name}_{column_name}", column_name)


def make_indexes() -> list[Index]:
    """
    Return a list of commonly-needed indexes.
    Add more specific composite indexes per-model as needed.
    """
    return []
