# models/cross_ref.py
"""Cross-reference model for the learning loop."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference table for learning/promotion logic."""

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_pattern_hash", "pattern_hash"),
        Index("ix_cross_ref_confirmed_at", "confirmed_at"),
    )

    po_line_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    invoice_vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    po_vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    vendor_match_score: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    
    invoice_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    po_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    description_match_score: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    
    invoice_item_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    po_item_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    item_match_score: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    
    invoice_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    quantity_variance_pct: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    quantity_match_score: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    
    invoice_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    po_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    price_variance_pct: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    price_match_score: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    
    overall_match_score: Mapped[float] = mapped_column(
        nullable=False,
    )
    match_decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    
    pattern_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    match_count: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )
    confirmed_at: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    promotion_weight: Mapped[float] = mapped_column(
        default=1.0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="cross_refs",
    )

    def __repr__(self) -> str:
        return f"<CrossRef score={self.overall_match_score} confirmed={self.confirmed_at}>"
