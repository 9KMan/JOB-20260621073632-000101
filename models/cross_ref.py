# models/cross_ref.py
"""
CrossRef SQLAlchemy model.

Learning loop table for confirmed matches that improve future matching accuracy.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross-Reference (Learning Loop) model.
    
    Stores confirmed matches that the system learns from.
    These entries improve future matching accuracy by:
    - Mapping non-standard SKU codes
    - Learning vendor-specific patterns
    - Storing historical match data
    - Tracking match quality over time
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_vendor_id", "vendor_id"),
        Index("ix_cross_ref_invoice_sku", "invoice_sku"),
        Index("ix_cross_ref_po_sku", "po_sku"),
        Index("ix_cross_ref_match_key", "vendor_id", "invoice_sku", "po_sku"),
        Index("ix_cross_ref_promotion_level", "promotion_level"),
        {"schema": None},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Identification
    # ─────────────────────────────────────────────────────────────────────────
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor identifier",
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # SKU Mapping
    # ─────────────────────────────────────────────────────────────────────────
    invoice_sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Invoice/vendor SKU",
    )
    invoice_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Invoice item description",
    )
    po_sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="PO SKU",
    )
    po_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="PO item description",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Price Reference
    # ─────────────────────────────────────────────────────────────────────────
    expected_unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Expected/standard unit price",
    )
    price_tolerance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Allowed price tolerance for this mapping",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Match Statistics
    # ─────────────────────────────────────────────────────────────────────────
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this mapping was used",
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of successful matches",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of failed matches",
    )
    
    @property
    def success_rate(self) -> Decimal:
        """Calculate success rate of this mapping."""
        if self.match_count == 0:
            return Decimal("0")
        return Decimal(str(self.success_count)) / Decimal(str(self.match_count))

    # ─────────────────────────────────────────────────────────────────────────
    # Promotion Level (Learning)
    # ─────────────────────────────────────────────────────────────────────────
    promotion_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="""
        Promotion level for learning:
        1 = New/Manual (requires confirmation)
        2 = Confirmed (auto-promoted after first success)
        3 = Trusted (multiple successes)
        4 = Verified (high confidence, rare overrides)
        """,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this mapping was used",
    )
    last_successful_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last successful match using this mapping",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Quality & Confidence
    # ─────────────────────────────────────────────────────────────────────────
    avg_match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Average match score for this mapping",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this mapping is active",
    )
    is_manual_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this is a manual user override",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────────────────
    confirmed_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who confirmed this mapping",
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this mapping was confirmed",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Notes about this mapping",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    source_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source invoice that created this mapping",
    )
    source_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source PO that created this mapping",
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef {self.vendor_id}: "
            f"{self.invoice_sku} -> {self.po_sku} "
            f"(level={self.promotion_level})>"
        )

    def record_match(self, success: bool, score: Optional[Decimal] = None) -> None:
        """
        Record a match attempt for this cross-reference.
        
        Args:
            success: Whether the match was successful
            score: Match score achieved
        """
        self.match_count += 1
        self.last_used_at = datetime.utcnow()
        
        if success:
            self.success_count += 1
            self.last_successful_at = datetime.utcnow()
            self.promote_if_eligible()
        else:
            self.failure_count += 1
            self.demote_if_needed()
        
        if score is not None:
            if self.avg_match_score is None:
                self.avg_match_score = score
            else:
                # Running average
                self.avg_match_score = (
                    (self.avg_match_score * (self.match_count - 1) + score)
                    / self.match_count
                )

    def promote_if_eligible(self) -> None:
        """Promote this mapping to a higher level if eligible."""
        if self.match_count >= 5 and self.success_rate >= Decimal("0.95"):
            self.promotion_level = min(self.promotion_level + 1, 4)

    def demote_if_needed(self) -> None:
        """Demote this mapping if failure rate is too high."""
        if self.match_count >= 3 and self.success_rate < Decimal("0.5"):
            self.promotion_level = max(self.promotion_level - 1, 1)
            self.is_active = self.promotion_level >= 2


from models.invoice import Invoice
from models.purchase_order import PurchaseOrder
