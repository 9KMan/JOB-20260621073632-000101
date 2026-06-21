# models/invoice.py
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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CommonMixin, SoftDeleteMixin
from models.enums import (
    InvoiceStatus,
    SourceSystem,
    get_invoice_status_enum,
    get_source_system_enum,
)

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, CommonMixin, SoftDeleteMixin):
    """Invoice model representing vendor invoices."""

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_vendor"),
        Index("ix_invoice_vendor_id", "vendor_id"),
        Index("ix_invoice_invoice_date", "invoice_date"),
        Index("ix_invoice_status", "status"),
        Index("ix_invoice_created_at", "created_at"),
        {"schema": None},
    )

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    vendor_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Vendor tax identification number",
    )

    # Invoice details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Vendor's invoice number",
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date on the invoice",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Payment due date",
    )
    receipt_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date invoice was received",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total invoice amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        get_invoice_status_enum(),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Amount matched to POs/delivery notes",
    )
    exception_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    # Source tracking
    source_system: Mapped[SourceSystem] = mapped_column(
        get_source_system_enum(),
        nullable=False,
        default=SourceSystem.MANUAL,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Reference from source system",
    )
    source_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp from source system",
    )

    # Additional fields
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_ocr_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    ocr_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="OCR confidence score (0-1)",
    )

    # Approved by
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict | None] = mapped_column(
        nullable=True,
        comment="Additional metadata as JSON",
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
        foreign_keys="CrossRef.invoice_id",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.vendor_id} - {self.status.value}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if invoice is fully matched."""
        return self.matched_amount >= self.total_amount

    @property
    def match_percentage(self) -> float:
        """Calculate match percentage."""
        if self.total_amount == 0:
            return 0.0
        return float(self.matched_amount / self.total_amount * 100)


class InvoiceLine(Base, CommonMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_line_invoice_id", "invoice_id"),
        Index("ix_invoice_line_po_line_id", "po_line_id"),
        Index("ix_invoice_line_dn_line_id", "dn_line_id"),
        {"schema": None},
    )

    # Parent invoice
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        comment="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Invoice quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Price per unit",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Total line amount",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Matching references
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="PO number reference",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Delivery note number reference",
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match status
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    # Product reference
    product_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if line is fully matched."""
        return self.matched_quantity >= self.quantity

    @property
    def variance_amount(self) -> Decimal:
        """Calculate amount variance."""
        expected = self.quantity * self.unit_price
        return self.line_amount - expected
