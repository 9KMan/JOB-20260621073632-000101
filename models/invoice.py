// models/invoice.py
"""Invoice model and related entities."""

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
    from models.delivery_note import DeliveryNoteLine
    from models.match import Match, MatchLine
    from models.purchase_order import PurchaseOrderLine


class Invoice(BaseModel):
    """Invoice model - one of the three documents in 3-way matching."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(
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
    
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    due_date: Mapped[Optional[date]] = mapped_column(
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
    
    amount_paid: Mapped[Decimal] = mapped_column(
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
    )  # pending, matched, approved, paid, disputed, cancelled
    
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="invoice",
    )
    
    balances: Mapped[List["Balance"]] = relationship(
        "Balance",
        back_populates="invoice",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate balance due on invoice."""
        return self.total_amount - self.amount_paid
    
    @property
    def line_count(self) -> int:
        """Get total number of lines."""
        return len(self.lines)


class InvoiceLine(BaseModel):
    """Individual line item in an Invoice."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
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
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
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
    
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    matched_po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    matched_dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
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
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    
    matched_po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_invoice_lines",
    )
    
    matched_dn_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_invoice_lines",
    )
    
    match_lines: Mapped[List["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="invoice_line",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.item_description[:30]}>"
