// src/app/models/invoice.py
"""
Invoice Model
Supplier invoices for AP processing.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Date, Numeric, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Invoice(BaseModel):
    """Invoice header."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
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
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="invoices")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
    )
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(BaseModel):
    """Invoice line item."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    delivery_note_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_lines",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"
