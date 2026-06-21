// models/invoice.py
"""
Invoice and InvoiceLine SQLAlchemy models.

Invoices represent bills received from vendors. Each invoice may contain
multiple line items that need to be matched against purchase orders
and delivery notes.
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
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import (
    InvoiceStatus,
    LineStatus,
    invoice_status_enum,
    line_status_enum,
)

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger


class Invoice(Base, UUIDMixin, TimestampMixin):
    """
    Invoice header table.
    
    Represents a vendor invoice received for payment processing.
    Each invoice contains one or more line items.
    """

    __tablename__ = "invoices"

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor's invoice number",
    )
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Vendor identifier code",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor display name",
    )

    # Financial details
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date on the invoice",
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
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
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total invoice amount including tax",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        invoice_status_enum,
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
        doc="Current invoice status",
    )
    matching_decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Matching engine decision",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Overall match confidence score (0-100)",
    )

    # Reference fields
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Anchored purchase order reference",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverynotes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Anchored delivery note reference",
    )

    # Metadata
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Invoice description or notes",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="External system reference (ERP, etc.)",
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment terms code",
    )
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

    # JSON metadata for extensibility
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        doc="Additional metadata as JSON",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoice_vendor_date", "vendor_code", "invoice_date"),
        Index("ix_invoice_status_match", "status", "match_score"),
        Index("ix_invoice_po_dn", "purchase_order_id", "delivery_note_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Invoice(id={self.id}, "
            f"invoice_number={self.invoice_number}, "
            f"vendor={self.vendor_code}, "
            f"amount={self.total_amount})>"
        )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """
    Invoice line item table.
    
    Represents individual line items on an invoice.
    Each line is matched against corresponding POL/DN lines.
    """

    __tablename__ = "invoice_lines"

    # Foreign key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )

    # Product/Service identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU or part number",
    )
    gtin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Global Trade Item Number",
    )

    # Financial details
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure code",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )

    # Matching details
    status: Mapped[LineStatus] = mapped_column(
        line_status_enum,
        nullable=False,
        default=LineStatus.OPEN,
        doc="Line matching status",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Line-level match confidence score",
    )
    matched_pol_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="Matched purchase order line ID",
    )
    matched_dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="Matched delivery note line ID",
    )

    # Metadata
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Tax classification code",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_invoice_line_invoice", "invoice_id", "line_number"),
        Index("ix_invoice_line_sku", "sku"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvoiceLine(id={self.id}, "
            f"line={self.line_number}, "
            f"sku={self.sku}, "
            f"qty={self.quantity})>"
        )
