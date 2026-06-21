// models/delivery_note.py
"""Delivery Note model and related entities."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.balance import Balance
    from models.invoice import InvoiceLine
    from models.match import Match, MatchLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(BaseModel):
    """Delivery Note model - one of the three documents in 3-way matching."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    supplier_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    po_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # Reference to PO number
    
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    received_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending, matched, completed, disputed, cancelled
    
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    carrier: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[Optional[dict]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON data
    
    # Relationships
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
    )
    
    balances: Mapped[List["Balance"]] = relationship(
        "Balance",
        back_populates="delivery_note",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"
    
    @property
    def line_count(self) -> int:
        """Get total number of lines."""
        return len(self.lines)


class DeliveryNoteLine(BaseModel):
    """Individual line item in a Delivery Note."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    item_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    item_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    matched_po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    matched_invoice_line_ids: Mapped[Optional[list]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON array of invoice line IDs
    
    match_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[Optional[dict]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON data
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    
    matched_po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_delivery_lines",
    )
    
    matched_invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_dn_line",
    )
    
    match_lines: Mapped[List["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="delivery_note_line",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.item_description[:30]}>"
    
    @property
    def quantity_accepted_or_delivered(self) -> Decimal:
        """Get accepted quantity if available, otherwise delivered quantity."""
        return self.quantity_accepted if self.quantity_accepted else self.quantity_delivered
