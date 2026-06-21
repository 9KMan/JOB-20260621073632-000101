// models/purchase_order.py
"""Purchase Order model and related entities."""

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
    from models.invoice import InvoiceLine
    from models.match import Match


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor/source of truth in 3-way matching."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(
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
    
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
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
        default="open",
        nullable=False,
    )  # open, partial, closed, cancelled
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[Optional[dict]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON data
    
    is_anchored: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="purchase_order",
    )
    
    balances: Mapped[List["Balance"]] = relationship(
        "Balance",
        back_populates="purchase_order",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount after matched invoices."""
        return self.total_amount
    
    @property
    def line_count(self) -> int:
        """Get total number of lines."""
        return len(self.lines)


class PurchaseOrderLine(BaseModel):
    """Individual line item in a Purchase Order."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
    
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    quantity_invoiced: Mapped[Decimal] = mapped_column(
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
    
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
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
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    
    matched_invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_po_line",
    )
    
    matched_delivery_lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_po_line",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.item_description[:30]}>"
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.quantity_ordered - self.quantity_delivered
    
    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity_ordered - self.quantity_invoiced
