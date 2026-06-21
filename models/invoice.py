// models/invoice.py
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing supplier invoices.

    Attributes:
        id: UUID primary key
        invoice_number: Unique invoice number from supplier
        supplier_id: External supplier identifier
        supplier_name: Name of the supplier
        invoice_date: Date on the invoice
        due_date: Payment due date
        total_amount: Total invoice amount
        currency: Currency code (ISO 4217)
        status: Current invoice status
        notes: Additional notes or comments
        purchase_order_id: Reference to matched purchase order (if any)
        matched_at: Timestamp when the invoice was matched
        matched_by: User who confirmed the match (if manual)
    """

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "supplier_id", name="uq_invoice_number_supplier"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_purchase_order_id", "purchase_order_id"),
        {"schema": None},
    )

    # Core fields
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Unique invoice number from the supplier",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="External supplier identifier",
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the supplier",
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
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        doc="Date the invoice was received in the system",
    )

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        doc="Total invoice amount",
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
        doc="Tax amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
        doc="Current invoice status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )

    # Matching references
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched purchase order",
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the invoice was matched",
    )
    matched_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who confirmed the match",
    )
    match_confidence: Mapped[float | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        doc="Match confidence score (0-100)",
    )

    # Relations
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
        foreign_keys=[purchase_order_id],
    )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice.

    Attributes:
        id: UUID primary key
        invoice_id: Parent invoice reference
        line_number: Line item number
        description: Item description
        quantity: Invoiced quantity
        unit_price: Price per unit
        total_amount: Line total (quantity * unit_price)
        purchase_order_line_id: Reference to matched PO line (if any)
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "purchase_order_line_id"),
        {"schema": None},
    )

    # Foreign key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent invoice reference",
    )

    # Line item details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number on the invoice",
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU or item code",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=4),
        nullable=False,
        doc="Price per unit",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    tax_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=True,
        doc="Tax rate percentage",
    )

    # Matching references
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched purchase order line",
    )
    matched_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=True,
        doc="Quantity matched to PO line",
    )

    # Relations
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )
