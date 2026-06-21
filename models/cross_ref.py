# models/cross_ref.py
"""Cross-reference table for learning and pattern matching."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.purchase_order import POLine


class CrossRef(Base, UUIDPrimaryKey, TimestampMixin):
    """
    Cross-reference table for learning loop / pattern matching.

    Stores confirmed matches between PO lines and invoice line characteristics
    to enable automatic pattern recognition in future matches.
    """

    __tablename__ = "cross_ref"

    # PO line reference
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Learned characteristics
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_pattern: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # Quantity and price characteristics
    typical_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    typical_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Matching statistics
    match_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_match_confidence: Mapped[float] = mapped_column(Numeric(10, 4), default=100.0)
    avg_match_confidence: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0)

    # Pattern strength (learned over time)
    strength: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    last_match_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Promotion tracking
    promotion_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Source tracking
    source_invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), default="learning", nullable=False)

    # Additional learned data
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    po_line_record: Mapped["POLine"] = relationship(
        "POLine", back_populates="cross_refs", foreign_keys=[po_line_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "vendor_code", "normalized_pattern", name="uq_cross_ref_vendor_pattern"
        ),
        Index("ix_cross_ref_strength", "strength"),
        Index("ix_cross_ref_promotion", "promotion_level"),
    )

    def promote(self) -> None:
        """Promote pattern to next strength level."""
        levels = ["new", "learning", "trained", "confirmed", "trusted"]
        current_idx = levels.index(self.strength) if self.strength in levels else 0
        if current_idx < len(levels) - 1:
            self.strength = levels[current_idx + 1]
            self.promotion_level += 1
            if self.strength == "confirmed":
                self.confirmed_at = datetime.utcnow()

    def update_confidence(self, new_confidence: float) -> None:
        """
        Update match statistics with new confidence score.

        Args:
            new_confidence: New match confidence score (0-100)
        """
        self.match_count += 1
        self.total_match_confidence += Decimal(str(new_confidence))
        self.avg_match_confidence = float(self.total_match_confidence) / self.match_count
        self.last_match_at = datetime.utcnow()
