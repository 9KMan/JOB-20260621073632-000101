# src/app/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
import uuid
import decimal
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Numeric, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.supplier import Supplier
    from src.app.models.user import User
    from src.app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.app.models.invoice import Invoice, InvoiceLine
    from src.app.models.matching import MatchResult
    from src.app.models.balance import BalanceLedger


class DeliveryNoteStatus:
    """Delivery Note status constants."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    RECEIVED = "RECEIVED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    CANCELLED = "CANCELLED"


class DeliveryNote(BaseModel):
    """Delivery Note / Goods Receipt header."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
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
    
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
        index=True,
    )
    
    delivery_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    received_date: Mapped[Optional[datetime]] = mapped_column(
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
        back_populates="delivery_notes",
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
        foreign_keys=[purchase_order_id],
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_notes",
        foreign_keys=[invoice_id],
    )
    
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="delivery_notes",
        foreign_keys="DeliveryNote.created_by",
    )
    
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    match_results: Mapped[List["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="delivery_note",
        foreign_keys="MatchResult.delivery_note_id",
    )
    
    balance_entries: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
        foreign_keys="BalanceLedger.delivery_note_id",
    )
    
    def calculate_totals(self) -> None:
        """Recalculate subtotal and total amounts from lines."""
        self.subtotal = sum(line.line_total for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        self.total_amount = self.subtotal + self.tax_amount
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, status={self.status})>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note line item."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
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
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
    )
    
    def calculate_totals(self) -> None:
        """Calculate line totals based on quantity and price."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * self.tax_rate
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, item={self.item_description}, qty={self.quantity})>"
