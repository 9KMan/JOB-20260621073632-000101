# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import BaseModel
from models.enums import InvoiceStatus, LineStatus


if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrderLine


class Invoice(BaseModel):
    """
    Invoice model representing supplier invoices.
    
    Attributes:
        invoice_number: Unique invoice identifier
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        invoice_date: Date on the invoice
        due_date: Payment due date
        subtotal: Invoice subtotal amount
        tax_amount: Tax amount
        total_amount: Total invoice amount
        currency: Currency code (ISO 4217)
        status: Current invoice status
        notes: Optional notes/comments
        matched_po_id: Reference to matched purchase order
        matched_dn_id: Reference to matched delivery note
        exception_count: Number of exceptions on this invoice
        matched_at: Timestamp when invoice was matched
    """

    __tablename__ = "invoices"

    # Core invoice fields
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique invoice number from vendor",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor identifier from ERP",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name",
    )
    
    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date on the invoice",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        doc="Date invoice was received in system",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Invoice subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total invoice amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(15, 6),
        nullable=False,
        default=Decimal("1.000000"),
        doc="Exchange rate to base currency",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
        doc="Current invoice status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes or comments",
    )

    # Matching references
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched purchase order",
    )
    matched_dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched delivery note",
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Match decision made",
    )
    match_score: Mapped[int | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Match score percentage",
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        doc="Timestamp when matched",
    )

    # Exception tracking
    exception_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        doc="Number of exceptions on this invoice",
    )

    # Approval workflow
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved the invoice",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        doc="Timestamp of approval",
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for rejection if rejected",
    )

    # ERP reference
    erp_invoice_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Invoice ID in ERP system",
    )
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment reference number",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_matched", "status", "matched_po_id"),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"


class InvoiceLine(BaseModel):
    """
    Invoice line item model.
    
    Attributes:
        line_number: Line item number
        description: Line item description
        quantity: Invoice quantity
        unit_price: Price per unit
        line_total: Total amount for this line
        matched_po_line_id: Reference to matched PO line
        matched_dn_line_id: Reference to matched delivery note line
        status: Line matching status
    """

    __tablename__ = "invoice_lines"

    # Parent reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to parent invoice",
    )

    # Line details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number",
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Invoice quantity",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total amount for this line",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Tax rate",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount for this line",
    )

    # Match references
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched PO line",
    )
    matched_dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched delivery note line",
    )
    match_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Type of match made",
    )
    match_score: Mapped[int | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Match score for this line",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        index=True,
        doc="Line matching status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Line-specific notes",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number"),
        Index("ix_invoice_lines_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line={self.line_number}, qty={self.quantity})>"
