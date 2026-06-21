# models/cross_ref.py
"""Cross-reference / learning loop table for match history and promotion."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Learning loop table — stores confirmed match relationships.

    When a match is approved by a human or auto-confirmed, it is stored here.
    The matching engine queries this table to "promote" patterns:
    - Same vendor + same description pattern → suggest match
    - Consistent price ratio → boost score
    - Consistent qty ratio → boost score
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_vendor_code", "vendor_code"),
        Index("ix_cross_ref_product_code", "product_code"),
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_match_count", "match_count"),
        Index(
            "ix_cross_ref_lookup",
            "vendor_code",
            "product_code",
            unique=True,
        ),
    )

    # ── Vendor / Product Identity ─────────────────────────────────────────────

    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Product / item identifiers
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_description_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Related Entities ──────────────────────────────────────────────────────

    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Learned Match Metrics ─────────────────────────────────────────────────

    # Count of successful matches using this cross-reference
    match_count: Mapped[int] = mapped_column(Integer, default=0)

    # Average match scores observed
    avg_match_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Learned ratios
    avg_price_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    avg_qty_ratio: Mapped[float] = mapped_column(Float, default=1.0)

    # Learned unit price (last known price)
    learned_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )

    # ── Status & Promotions ───────────────────────────────────────────────────

    # Whether this cross-ref is confirmed/active
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Number of promotions (promoted patterns get higher scores)
    promotion_level: Mapped[int] = mapped_column(Integer, default=0)

    # Last used
    last_matched_at: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Auto-generated pattern flag
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    def promote(self) -> None:
        """Increment promotion level after a confirmed match."""
        self.match_count += 1
        self.promotion_level = min(self.promotion_level + 1, 10)
        self.is_promoted = self.promotion_level >= 3

    def __repr__(self) -> str:
        return (
            f"<CrossRef vendor={self.vendor_code} product={self.product_code} "
            f"matches={self.match_count} promoted={self.is_promoted}>"
        )
