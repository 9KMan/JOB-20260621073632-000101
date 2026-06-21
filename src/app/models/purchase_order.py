# src/app/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""
import uuid
import decimal
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Numeric, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.supplier import Supplier
    from src.app.models.user import User
    from src.app.models.invoice import Invoice, InvoiceLine
    from src.app.models.delivery_note import DeliveryNote, DeliveryNoteLine
    from src.app.models.matching import MatchResult
    from src.app.models.balance import BalanceLedger


class PurchaseOrderStatus:
    """Purchase Order status constants."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(BaseModel):
    """Purchase Order header."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )
    
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    subtotal: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="purchase_orders",
    )
    
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="purchase_orders",
        foreign_keys="PurchaseOrder.created_by",
    )
    
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        foreign_keys="Invoice.purchase_order_id",
    )
    
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        foreign_keys="DeliveryNote.purchase_order_id",
    )
    
    match_results: Mapped[List["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="purchase_order",
        foreign_keys="MatchResult.purchase_order_id",
    )
    
    balance_entries: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        foreign_keys="BalanceLedger.purchase_order_id",
    )
    
    def calculate_totals(self) -> None:
        """Recalculate subtotal and total amounts from lines."""
        self.subtotal = sum(line.line_total for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        self.total_amount = self.subtotal + self.tax_amount
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, status={self.status})>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    
    quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    
    tax_rate: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    line_total: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    received_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    
    invoiced_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="purchase_order_line",
    )
    
    delivery_note_lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="purchase_order_line",
    )
    
    def calculate_totals(self) -> None:
        """Calculate line totals based on quantity and price."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * self.tax_rate
    
    @property
    def remaining_quantity(self) -> decimal.Decimal:
        """Get remaining quantity not yet received."""
        return self.quantity - self.received_quantity
    
    @property
    def remaining_invoiced_quantity(self) -> decimal.Decimal:
        """Get remaining quantity not yet invoiced."""
        return self.quantity - self.invoiced_quantity
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, item={self.item_description}, qty={self.quantity})>"
