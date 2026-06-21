# src/models/invoice.py
"""Invoice model for AP Automation Core Engine.

Represents supplier invoices that need to be matched against
purchase orders and delivery notes.
"""

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
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class InvoiceLine(TimestampMixin, UUIDMixin, Base):
    """Individual line item on an invoice.

    Each invoice can have multiple line items that correspond to
    PO lines for matching purposes.
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to parent invoice",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure (e.g., EA, KG, M)",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Tax amount for this line",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched PO line ID (populated after matching)",
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched delivery note line ID",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Matching confidence score (0-1)",
    )
    match_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        doc="Line matching status",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
        foreign_keys=[invoice_id],
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_match_status", "match_status"),
    )


class Invoice(TimestampMixin, SoftDeleteMixin, UUIDMixin, Base):
    """Invoice model representing supplier invoices.

    Contains header information and links to line items for matching
    against purchase orders and delivery notes.
    """

    __tablename__ = "invoices"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Vendor/supplier identifier from ERP",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor/supplier name",
    )
    vendor_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Vendor tax identification number",
    )

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Invoice number from vendor",
    )
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
        doc="Date invoice was received in system",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoice subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Total tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoice total (subtotal + tax)",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        doc="Invoice status",
    )
    match_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        doc="Matching process status",
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Matching decision type",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Overall matching confidence score (0-1)",
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when matching was completed",
    )

    # ERP reference
    erp_invoice_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Invoice ID in the ERP system",
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
        doc="Source system identifier",
    )

    # Payment information
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment terms (e.g., Net 30)",
    )
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment reference number",
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Amount paid so far",
    )

    # Additional metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User who approved the invoice",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when approved",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_match_status", "match_status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_erp_invoice_id", "erp_invoice_id"),
        Index("ix_invoices_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} from {self.vendor_name}>"
