# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrderLine
    from models.delivery_note import DeliveryNoteLine


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Invoice header model.
    
    Represents a supplier invoice received for payment processing.
    """
    
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
    )
    
    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Invoice Identification
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Financial Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Status and Processing
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50),
        nullable=False,
        default=InvoiceStatus.PENDING,
    )
    
    # Matching Results
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Source Information
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Additional Fields
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Payment Information
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Invoice line item model.
    
    Represents individual line items on an invoice.
    """
    
    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_dn_line_id", "dn_line_id"),
    )
    
    # Parent Invoice
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Line Information
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    
    # Matching References
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Matching Results
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
        foreign_keys=[po_line_id],
    )
    dn_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_lines",
        foreign_keys=[dn_line_id],
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )
