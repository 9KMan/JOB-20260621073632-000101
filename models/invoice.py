// models/invoice.py
"""Invoice model definition."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Date,
    Numeric,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice model representing supplier invoices.
    
    Attributes:
        id: UUID primary key
        invoice_number: Unique invoice identifier
        supplier_id: External supplier identifier
        supplier_name: Supplier name
        invoice_date: Date on the invoice
        due_date: Payment due date
        total_amount: Total invoice amount
        tax_amount: Tax amount
        currency: Currency code (e.g., USD, EUR)
        status: Current invoice status
        notes: Additional notes
        erp_reference: External ERP system reference
        matched_po_id: Reference to matched purchase order
        match_score: Calculated match score (0-100)
        match_decision: Matching decision outcome
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_matched_po_id", "matched_po_id"),
    )
    
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50),
        default=InvoiceStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    erp_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
        foreign_keys=[matched_po_id],
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
    )


class InvoiceLineItem(Base, UUIDMixin, TimestampMixin):
    """Line items for invoices.
    
    Attributes:
        id: UUID primary key
        invoice_id: Parent invoice reference
        line_number: Line item sequence number
        description: Item description
        quantity: Invoiced quantity
        unit_price: Price per unit
        amount: Total line amount
        uom: Unit of measure
        tax_code: Tax classification code
    """
    
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        Index("ix_invoice_line_items_invoice_id", "invoice_id"),
    )
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="line_items",
    )
