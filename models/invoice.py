# models/invoice.py
"""
Invoice and InvoiceLine SQLAlchemy models.

Represents AP invoices and their line items for matching.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Invoice model representing AP invoices from vendors.
    
    An invoice contains multiple line items that need to be matched
    against purchase orders and delivery notes.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_vendor_invoice_number", "vendor_id", "invoice_number", unique=True),
        {"schema": None},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Core Fields
    # ─────────────────────────────────────────────────────────────────────────
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor/Supplier identifier from ERP",
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor display name",
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Invoice number from vendor",
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date on the invoice",
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Financial Fields
    # ─────────────────────────────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
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
        default=Decimal("0.00"),
        doc="Invoice total amount",
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Amount paid so far",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Status & Workflow
    # ─────────────────────────────────────────────────────────────────────────
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
        doc="Current invoice status",
    )
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether invoice has been matched",
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when matching was completed",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Matching Results
    # ─────────────────────────────────────────────────────────────────────────
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Overall match score (0.0000 to 1.0000)",
    )
    match_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Match decision (auto_approve, review, exception, no_match)",
    )
    matched_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched purchase order ID",
    )
    matched_dn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched delivery note ID",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────────────────
    erp_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="ERP system reference number",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created the invoice",
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved the invoice",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of approval",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[matched_po_id],
        backref="matched_invoices",
    )
    matched_dn: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[matched_dn_id],
        backref="matched_invoices",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} from {self.vendor_id}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """
    Invoice line item model.
    
    Represents individual line items on an invoice that need
    to be matched against PO lines.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Foreign Keys
    # ─────────────────────────────────────────────────────────────────────────
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Line Details
    # ─────────────────────────────────────────────────────────────────────────
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number on invoice",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product/Item SKU",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure (EA, KG, etc.)",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Pricing
    # ─────────────────────────────────────────────────────────────────────────
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Tax rate as decimal (0.2000 = 20%)",
    )
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Tax amount for this line",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Matching
    # ─────────────────────────────────────────────────────────────────────────
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched PO line ID",
    )
    dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched DN line ID",
    )
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this line has been matched",
    )
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Match score for this line",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
        backref="matched_invoice_lines",
    )
    dn_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        foreign_keys=[dn_line_id],
        backref="matched_invoice_lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
