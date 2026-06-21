# models/invoice.py
"""Invoice model for AP Automation Engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing supplier invoices.

    Attributes:
        invoice_number: Unique invoice number from supplier
        vendor_id: External vendor identifier
        vendor_name: Name of the vendor
        invoice_date: Date on the invoice
        due_date: Payment due date
        subtotal: Invoice subtotal before tax
        tax_amount: Tax amount
        total_amount: Total invoice amount
        currency: Currency code (e.g., USD, EUR)
        status: Current invoice status
        match_status: Status of matching process
        match_score: Calculated match score (0.0 - 1.0)
        decision: Matching engine decision
        po_reference: Reference to linked PO
        dn_reference: Reference to linked delivery note
        notes: Additional notes
        approved_by: User who approved (if applicable)
        approved_at: Timestamp of approval
        metadata: JSON metadata for extensibility
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_match_status", "match_status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
    )

    # Basic Information
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        doc="Unique invoice number",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="External vendor identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the vendor",
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

    # Financial Information
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

    # Status and Matching
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        doc="Current invoice status",
    )
    match_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        doc="Status of matching process",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Calculated match score (0.0 - 1.0)",
    )
    decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Matching engine decision",
    )
    confidence: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Match confidence level",
    )

    # References
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Linked purchase order ID",
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Purchase order number",
    )
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        doc="Linked delivery note ID",
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Delivery note number",
    )

    # Approval
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved the invoice",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of approval",
    )

    # Additional Information
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="JSON metadata for extensibility",
    )
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when invoice was received",
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
        doc="Source system (erp, ocr, manual)",
    )

    # Relationships
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        foreign_keys="BalanceLedger.invoice_id",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        foreign_keys="CrossRef.invoice_id",
    )


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Invoice line item model.

    Attributes:
        invoice_id: Parent invoice ID
        line_number: Line item number
        description: Item description
        quantity: Invoice quantity
        unit_price: Price per unit
        amount: Total line amount
        tax_code: Tax code
        po_line_id: Reference to PO line
        dn_line_id: Reference to delivery note line
        matched_qty: Quantity matched
        match_status: Match status for this line
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent invoice ID",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoice quantity",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Tax code",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Line tax amount",
    )

    # Matching References
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to PO line",
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to delivery note line",
    )

    # Match Tracking
    matched_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity matched",
    )
    match_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        doc="Match status for this line",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Match score for this line",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )


# Add JSONB import at runtime to avoid compatibility issues
from sqlalchemy.dialects.postgresql import JSONB

Invoice.__table__.c.metadata = Base.metadata
InvoiceLine.__table__.c.metadata = Base.metadata
