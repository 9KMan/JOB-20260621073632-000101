# src/models/invoice.py
"""Invoice model and related types."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Invoice model representing supplier invoices.
    
    Attributes:
        id: Unique identifier (UUID)
        invoice_number: Supplier's invoice number
        supplier_id: External supplier identifier
        supplier_name: Supplier's business name
        invoice_date: Date on the invoice
        due_date: Payment due date
        currency: ISO currency code (e.g., USD, EUR)
        subtotal: Sum of line amounts before tax
        tax_amount: Total tax amount
        total_amount: Grand total (subtotal + tax)
        status: Current invoice status
        vendor_reference: Vendor's internal reference
        payment_terms: Payment terms description
        notes: Additional notes/comments
        metadata: JSON field for additional data
        matched_at: Timestamp when invoice was matched
        matched_by: User/system that performed matching
    """
    
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_supplier_invoice", "supplier_id", "invoice_number", unique=True),
    )
    
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
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
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "pending",
            "received",
            "matching",
            "matched",
            "approved",
            "exception",
            "rejected",
            "paid",
            "cancelled",
            name="invoice_status",
            create_constraint=True,
        ),
        nullable=False,
        default="draft",
        index=True,
    )
    vendor_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    matched_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
    )


class InvoiceLine(UUIDMixin, TimestampMixin, Base):
    """
    Individual line item on an invoice.
    
    Attributes:
        id: Unique identifier (UUID)
        invoice_id: Parent invoice reference
        line_number: Line item sequence number
        description: Line item description
        product_code: Supplier's product/SKU code
        quantity: Invoiced quantity
        unit_of_measure: UOM (e.g., EA, KG, BOX)
        unit_price: Price per unit
        tax_code: Tax classification code
        tax_rate: Tax rate percentage
        line_total: Calculated line total
        po_line_id: Matched PO line reference
        delivery_line_id: Matched delivery line reference
        match_status: Line-level match status
        match_score: Confidence score for the match
    """
    
    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_product_code", "product_code"),
    )
    
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
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
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    po_line_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_line_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_status: Mapped[str] = mapped_column(
        Enum(
            "unmatched",
            "partial_match",
            "full_match",
            "over_matched",
            "multiple_matches",
            name="line_match_status",
            create_constraint=True,
        ),
        nullable=False,
        default="unmatched",
    )
    match_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    delivery_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        foreign_keys=[delivery_line_id],
    )
