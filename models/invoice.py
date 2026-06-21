// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus, LineStatus, MatchStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_supplier_number", "supplier_number"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_created_at", "created_at"),
        Index("ix_invoices_external_reference", "external_reference"),
        {
            "schema": "public",
        },
    )

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Supplier's invoice number",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="External system reference (ERP, OCR, etc.)",
    )

    # Supplier information
    supplier_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Internal supplier identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Supplier name",
    )
    supplier_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Supplier account number",
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Invoice date from supplier",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )
    posting_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date to post to GL",
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total invoice amount including tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount",
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Net invoice amount before tax",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status and processing
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.PENDING,
        doc="Invoice processing status",
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        String(20),
        nullable=False,
        default=MatchStatus.PENDING,
        doc="Matching status",
    )
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating potential duplicate",
    )

    # Additional metadata
    payment_terms: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Payment terms code",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Invoice description or notes",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # User who created/modified
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created the invoice",
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
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
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
        Index("ix_invoice_lines_product_code", "product_code"),
        {
            "schema": "public",
        },
    )

    # Parent reference
    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent invoice ID",
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    external_line_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="External system line reference",
    )

    # Product/Service information
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product or service code",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total line amount",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Tax rate percentage",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Line tax amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line matching status",
    )
    match_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Match confidence score (0-100)",
    )

    # Matched references
    matched_po_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        doc="Matched PO line ID",
    )
    matched_delivery_note_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        doc="Matched delivery note line ID",
    )

    # Variance tracking
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Price variance from PO",
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Quantity variance from PO",
    )

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, invoice_id={self.invoice_id}, line={self.line_number})>"
