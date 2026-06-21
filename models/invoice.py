// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

This module defines the Invoice and InvoiceLine database models
for storing invoice data and line items.
"""

import uuid
from datetime import date, datetime, timezone
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DecisionType, DocumentStatus, MatchStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing a vendor invoice.

    Attributes:
        invoice_number: Unique invoice number from vendor
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        invoice_date: Date on the invoice
        due_date: Payment due date
        subtotal: Invoice subtotal before tax
        tax_amount: Tax amount
        total_amount: Total invoice amount
        currency: Currency code (ISO 4217)
        status: Current document status
        match_status: Status of matching process
        match_score: Match confidence score (0-100)
        decision: Final decision from matching engine
        po_reference: Referenced PO number if available
        notes: Additional notes
        lines: Invoice line items
        cross_refs: Cross-reference records for matches
        balance_ledgers: Balance ledger entries
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_match_status", "match_status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_number_vendor"),
    )

    # Core fields
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        default_factory=lambda: date.today(),
        nullable=False,
    )

    # Financial fields
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Status fields
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    match_status: Mapped[str] = mapped_column(
        String(30),
        default=MatchStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    match_score: Mapped[int | None] = mapped_column(
        default=None,
        nullable=True,
    )
    decision: Mapped[str | None] = mapped_column(
        String(30),
        default=None,
        nullable=True,
    )

    # Reference fields
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice for
    line-level matching with purchase orders.

    Attributes:
        invoice_id: Parent invoice foreign key
        line_number: Line item number on invoice
        description: Line item description
        quantity: Invoiced quantity
        unit_of_measure: Unit of measure
        unit_price: Price per unit
        total_price: Line total (quantity * unit_price)
        tax_rate: Tax rate percentage
        tax_amount: Tax amount for line
        po_line_id: Matching PO line ID if anchored
        matched_quantity: Quantity matched to PO
        match_score: Line-level match score
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

    # Foreign key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Quantity and pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Tax
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Matching
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    matched_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    match_score: Mapped[int | None] = mapped_column(
        default=None,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.description[:30]}>"
