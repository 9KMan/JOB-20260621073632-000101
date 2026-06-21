"""Declarative base + shared mixins.

We pin UUID primary keys (per spec) and enforce ``created_at``/``updated_at``
on every table. Soft-delete is opt-in via :class:`SoftDeleteMixin` so models
that need it (e.g. exceptions) can include it explicitly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Stable naming convention keeps Alembic diffs minimal.
NAMING_CONVENTION: dict[str, Any] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _utcnow() -> datetime:
    """Timezone-aware UTC now (database column expects tz-aware datetimes)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Project-wide declarative base."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {uuid.UUID: PG_UUID(as_uuid=True)}


class UUIDPrimaryKeyMixin:
    """UUID primary key with database-side default."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` columns maintained on the server."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


class SoftDeleteMixin:
    """Opt-in soft delete. ``deleted_at`` is null when the row is active."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    @declared_attr
    def __mapper_args__(cls) -> dict[str, Any]:  # noqa: N805
        return {"eager_defaults": True}

    def soft_delete(self) -> None:
        self.deleted_at = _utcnow()

    def restore(self) -> None:
        self.deleted_at = None
