# models/invoice.py
# Invoice table and SQLAlchemy model
# AP Automation Core Engine — FinaRo

"""Invoice and InvoiceLine SQLAlchemy ORM models."""

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import (
    InvoiceStatus,
    InvoiceStatusType,
    LineStatus,
    LineStatusType,
)

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine
    from models.delivery_note import DeliveryNoteLine
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing a supplier invoice.

    Attributes:
        id: UUID primary key.
        invoice_number: Unique invoice number from the supplier.
        vendor_id: External vendor/system identifier.
        vendor_name: Vendor name for display purposes.
        vendor_address: Vendor address (optional).
        invoice_date: Date on the invoice.
        due_date: Payment due date.
        subtotal: Invoice subtotal before tax.
        tax_amount: Tax amount.
        total_amount: Total invoice amount.
        currency: Currency code (e.g., USD, EUR).
        status: Current invoice status.
        po_reference: Reference to the associated PO (optional).
        notes: Additional notes.
        is_credit_memo: Whether this is a credit memo.
        matched_at: Timestamp when matching was completed.
        approved_at: Timestamp when invoice was approved.
        approved_by: User who approved the invoice.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
        deleted_at: Soft delete timestamp.
    """

    __tablename__ = "invoices"

    # Basic invoice info
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Unique invoice number from supplier",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="External vendor/system identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name for display",
    )
    vendor_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Vendor address",
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date on the invoice",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Subtotal before tax",
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
        index=True,
        doc="Total invoice amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        InvoiceStatusType,
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
        doc="Current invoice status",
    )
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Reference to associated PO",
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    is_credit_memo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this is a credit memo",
    )

    # Matching and approval timestamps
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when matching was completed",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when invoice was approved",
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved the invoice",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Invoice line items",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_invoice", "vendor_id", "invoice_number", unique=True),
        Index("ix_invoices_status_created", "status", "created_at"),
        Index("ix_invoices_invoice_date", "invoice_date"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Attributes:
        id: UUID primary key.
        invoice_id: Parent invoice UUID.
        line_number: Line item number.
        description: Item description.
        quantity: Invoiced quantity.
        unit_price: Price per unit.
        total_amount: Line total (quantity * unit_price).
        uom: Unit of measure.
        po_line_id: Reference to matched PO line (optional).
        delivery_line_id: Reference to matched delivery line (optional).
        status: Line matching status.
        match_score: Matching confidence score (0-1).
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "invoice_lines"

    # Foreign key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent invoice UUID",
    )

    # Line info
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
        doc="Invoiced quantity",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    uom: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure",
    )

    # Matching references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched PO line",
    )
    delivery_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched delivery line",
    )

    # Matching status
    status: Mapped[LineStatus] = mapped_column(
        LineStatusType,
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line matching status",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Matching confidence score (0-1)",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
        doc="Parent invoice",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number"),
        Index("ix_invoice_lines_po_line", "po_line_id"),
        Index("ix_invoice_lines_delivery_line", "delivery_line_id"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.description[:30]}>"
