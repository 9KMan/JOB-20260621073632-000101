// models/cross_ref.py
"""Cross-reference model for learning and match history."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference table for learning loop and match history.
    
    Stores confirmed matches between invoices and POs to improve
    future matching accuracy through learning.
    
    Attributes:
        id: UUID primary key
        invoice_id: Invoice reference
        po_id: Purchase order reference
        invoice_line_number: Matched invoice line number
        po_line_id: Matched PO line item reference
        supplier_id: Supplier identifier
        supplier_part_number: Supplier's part number
        po_part_description: PO line description
        match_count: Number of times this match has been confirmed
        total_quantity: Cumulative matched quantity
        average_price: Average matched price
        last_matched_at: Most recent match timestamp
        is_promoted: Whether this match is promoted for priority
        confidence_score: Calculated confidence score
        is_active: Whether this cross-reference is active
    """
    
    __tablename__ = "cross_refs"
    __table_args__ = (
        Index("ix_cross_refs_invoice_id", "invoice_id"),
        Index("ix_cross_refs_po_id", "po_id"),
        Index("ix_cross_refs_supplier_id", "supplier_id"),
        Index("ix_cross_refs_supplier_part", "supplier_id", "supplier_part_number"),
        Index("ix_cross_refs_match_count", "match_count"),
        Index("ix_cross_refs_is_promoted", "is_promoted"),
    )
    
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_number: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("purchase_order_line_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    po_part_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    match_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    total_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    average_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    last_matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=0.0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    confirmation_notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
    )
