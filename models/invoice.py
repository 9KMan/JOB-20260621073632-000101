// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Represents vendor invoices with line items for matching
against purchase orders and delivery notes.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import Currency, InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Vendor invoice model.

    Contains header information and relationships to line items.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
        UniqueConstraint("vendor_id", "invoice_number", name="uq_vendor_invoice"),
    )

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor/supplier identifier from ERP",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor display name",
    )
    vendor_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Vendor tax identification number",
    )

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Vendor's invoice number",
    )
    invoice_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Invoice date (YYYY-MM-DD)",
    )
    due_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Payment due date (YYYY-MM-DD)",
    )

    # Financial Information
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )
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
        doc="Total tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Invoice total amount",
    )
    tax_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Tax rate applied (e.g., 0.0825 for 8.25%)",
    )

    # Status and Processing
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.DRAFT.value,
        index=True,
        doc="Current invoice status",
    )
    matching_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Matching engine decision",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Match confidence score (0-100)",
    )

    # Additional Fields
    payment_terms: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Payment terms (e.g., NET 30)",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )
    is_credit_memo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this is a credit memo",
    )

    # Reconciliation
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched purchase order ID",
    )
    matched_dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched delivery note ID",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} from {self.vendor_id}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Individual line item on an invoice.

    Each line represents a single product or service with
    quantity and price information.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "invoice_id", "line_number"),
    )

    # Foreign Key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent invoice ID",
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )

    # Product Information
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU/UPC",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Internal product code",
    )
    barcode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product barcode",
    )

    # Quantity and Pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("1"),
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure (e.g., EA, KG, M)",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount (qty * unit_price)",
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Line-level tax amount",
    )

    # Matching Reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched purchase order line ID",
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched delivery note line ID",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.sku or 'No SKU'}>"
