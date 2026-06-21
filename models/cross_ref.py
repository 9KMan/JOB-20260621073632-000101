# models/cross_ref.py
"""Cross Reference model for the learning loop functionality."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import MatchDecision, MatchConfidence

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class CrossRef(TimestampMixin, UUIDPrimaryKeyMixin, Base):
    """Cross Reference table for learning/promotion functionality.

    This table tracks confirmed matches between invoice lines and PO lines,
    building a historical record that can be used to:
    - Learn supplier-specific patterns
    - Promote confirmed matches for future automatic matching
    - Build confidence scores based on historical accuracy
    """

    __tablename__ = "cross_ref"

    # Source records
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Product matching
    invoice_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    sku_match_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Supplier info
    supplier_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Match metrics
    price_variance_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    quantity_variance_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    match_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    match_decision: Mapped[MatchDecision | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Status
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    confirmation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Promotion tracking
    promotion_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    """Promotion level: 0=new, 1=promoted once, 2=promoted twice, etc."""
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    """How many times this exact match has been confirmed"""
    auto_match_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )
    """Threshold score at which this cross_ref enables auto-match"""

    # Learning data
    last_matched_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    first_matched_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Confidence
    confidence: Mapped[MatchConfidence] = mapped_column(
        String(20),
        nullable=False,
        default=MatchConfidence.NONE,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="cross_refs",
    )

    __table_args__ = (
        Index("ix_cross_ref_supplier_sku", "supplier_id", "po_sku"),
        Index("ix_cross_ref_invoice_sku", "invoice_sku"),
        Index("ix_cross_ref_promotion", "is_active", "match_count"),
        Index("ix_cross_ref_confirmed", "is_confirmed", "supplier_id"),
    )

    def __repr__(self) -> str:
        return f"<CrossRef SKU:{self.po_sku} Supplier:{self.supplier_id} Count:{self.match_count}>"

    def should_auto_match(self, score: int) -> bool:
        """Determine if this cross_ref enables auto-matching.

        Args:
            score: Current match score

        Returns:
            True if match should be automatic
        """
        if not self.is_active or not self.is_confirmed:
            return False
        return score >= self.auto_match_threshold

    def promote(self) -> None:
        """Promote this cross_ref to higher auto-match confidence."""
        self.promotion_level += 1
        self.match_count += 1
        # Increase threshold for auto-match as confidence grows
        # Level 0: 95+, Level 1: 90+, Level 2: 85+, etc.
        self.auto_match_threshold = max(50, 100 - (self.promotion_level * 5))
        self.confidence = self._calculate_confidence()

    def confirm(self, confirmation_date: date | None = None) -> None:
        """Confirm this cross_ref match.

        Args:
            confirmation_date: When the match was confirmed
        """
        self.is_confirmed = True
        self.confirmation_date = confirmation_date or date.today()
        if not self.first_matched_date:
            self.first_matched_date = self.confirmation_date
        self.last_matched_date = self.confirmation_date
        self.promote()

    def _calculate_confidence(self) -> MatchConfidence:
        """Calculate confidence level based on match count and promotion level."""
        if self.match_count >= 10 and self.promotion_level >= 2:
            return MatchConfidence.EXACT
        elif self.match_count >= 5 and self.promotion_level >= 1:
            return MatchConfidence.HIGH
        elif self.match_count >= 2:
            return MatchConfidence.MEDIUM
        elif self.match_count >= 1:
            return MatchConfidence.LOW
        return MatchConfidence.NONE


__all__ = ["CrossRef"]
