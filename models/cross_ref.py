"""Cross-reference learning table.

Each row records a confirmed (vendor_id, sku, description) alias triple that
the matching engine can promote into a fast-path rule. Promotion happens when
a triple has accumulated at least ``cross_ref_min_confirmations`` confirmed
matches and the average confidence exceeds ``cross_ref_promotion_threshold``.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CrossRef(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A vendor-aware (sku <-> description) alias used by the learning loop."""

    __tablename__ = "cross_ref"

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    canonical_description: Mapped[str] = mapped_column(String(1024), nullable=False)
    alias_description: Mapped[str] = mapped_column(String(1024), nullable=False)
    confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    is_promoted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen_at: Mapped[Decimal] = mapped_column(
        Numeric(20, 6),
        nullable=False,
        default=Decimal("0"),
        doc="Unix epoch seconds of most recent confirmation (numeric for portability).",
    )

    __table_args__ = (
        UniqueConstraint(
            "vendor_id",
            "sku",
            "alias_description",
            name="ux_cross_ref_vendor_sku_alias",
        ),
        Index("ix_cross_ref_vendor_sku_promoted", "vendor_id", "sku", "is_promoted"),
    )
