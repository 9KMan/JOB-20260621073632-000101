# models/invoice.py
"""
Invoice and InvoiceLine SQLAlchemy models.

Represents AP invoices received from suppliers, with line items
that will be matched against purchase orders and delivery notes.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base):
    """
    Invoice header model.
    
    Represents a supplier invoice that needs to be matched
    against purchase orders and/or delivery notes.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_supplier_number", "supplier_number"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
        UniqueConstraint("supplier_number", "invoice_number", name="uq_invoice_supplier_number"),
        {"schema": None},
    )

    # Invoice identification
    supplier_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Supplier/Vendor ID in the ERP system",
    )

    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Supplier/Vendor number",
    )

    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Supplier/Vendor name",
    )

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Supplier's invoice number",
    )

    # Financial amounts
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Invoice date from supplier",
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Payment due date",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Invoice subtotal before tax",
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Tax amount",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Total invoice amount including tax",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
        comment="Current invoice status",
    )

    # Matching results
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Amount matched to POs/DNs",
    )

    match_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        comment="Match percentage (0-100)",
    )

    # Source information
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Source system identifier (ERP, OCR, etc.)",
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Original reference in source system",
    )

    # OCR/extraction metadata
    ocr_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="OCR confidence score (0-100)",
    )

    # Approval workflow
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="User who approved the invoice",
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Approval timestamp",
    )

    # Notes and metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes",
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional metadata as JSON",
    )

    # Payment information
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Payment reference number",
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Payment timestamp",
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
        foreign_keys="CrossRef.invoice_id",
        cascade="all, delete-orphan",
    )

    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} from {self.supplier_number}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if invoice is fully matched."""
        return self.match_percentage >= 100.0

    @property
    def is_partially_matched(self) -> bool:
        """Check if invoice is partially matched."""
        return 0 < self.match_percentage < 100.0

    @property
    def unmatched_amount(self) -> Decimal:
        """Calculate unmatched amount."""
        return self.total_amount - self.matched_amount


class InvoiceLine(Base):
    """
    Invoice line item model.
    
    Represents individual line items on an invoice that
    can be matched against PO and delivery note lines.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
        Index("ix_invoice_lines_product_code", "product_code"),
        {"schema": None},
    )

    # Parent reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Line item number on the invoice",
    )

    # Product information
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product/SKU code",
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Line item description",
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Invoiced quantity",
    )

    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure (EA, KG, etc.)",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Unit price",
    )

    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Line total (quantity * unit_price)",
    )

    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Tax code",
    )

    # Matching state
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity matched to PO/DN lines",
    )

    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Amount matched",
    )

    # Cross-references (denormalized for performance)
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Matched PO line ID",
    )

    matched_dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Matched delivery note line ID",
    )

    # Relationship
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.product_code} x {self.quantity}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if line is fully matched."""
        return self.matched_quantity >= self.quantity

    @property
    def unmatched_quantity(self) -> Decimal:
        """Calculate unmatched quantity."""
        return self.quantity - self.matched_quantity

    @property
    def match_percentage(self) -> float:
        """Calculate match percentage for this line."""
        if self.quantity == 0:
            return 100.0
        return float((self.matched_quantity / self.quantity) * 100)
