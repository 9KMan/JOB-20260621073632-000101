// models/cross_ref.py
"""Cross Reference table for the learning loop functionality."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference table for learned matches and patterns."""

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_item_code", "item_code"),
        Index("ix_cross_ref_confirmed_count", "confirmed_count"),
    )

    # Foreign keys
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match criteria
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    item_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Matched prices
    po_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    matched_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    price_variance_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0.00"))
    
    # Matched quantities
    po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_variance_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0.00"))
    
    # Confidence and learning
    base_confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    current_confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    confirmed_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Promotion tracking
    promotion_level: Mapped[int] = mapped_column(Integer, default=0)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Pattern info
    match_type: Mapped[str] = mapped_column(String(30), nullable=False)
    match_method: Mapped[str] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship("PurchaseOrderLine")
    invoice_line: Mapped["InvoiceLine | None"] = relationship("InvoiceLine")

    def promote_confidence(self, boost_amount: float) -> None:
        """Increase confidence when a match is confirmed."""
        self.confirmed_count += 1
        self.current_confidence = min(100.0, self.current_confidence + boost_amount)
        self.last_confirmed_at = datetime.utcnow()
        
        # Promote to next level after enough confirmations
        if self.confirmed_count >= 3 and self.promotion_level == 0:
            self.promotion_level = 1
        elif self.confirmed_count >= 5 and self.promotion_level == 1:
            self.promotion_level = 2

    def demote_confidence(self, penalty_amount: float) -> None:
        """Decrease confidence when a match is rejected."""
        self.rejected_count += 1
        self.current_confidence = max(0.0, self.current_confidence - penalty_amount)
        self.last_rejected_at = datetime.utcnow()
        
        # Reset promotion level on rejection
        if self.rejected_count >= 2:
            self.promotion_level = max(0, self.promotion_level - 1)
