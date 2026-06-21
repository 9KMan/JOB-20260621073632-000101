# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Represents AP invoices and their line items for the matching engine.
"""

from datetime import date, datetime
from decimal import Decimal
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice model representing accounts payable invoices.

    Attributes:
        vendor_id: External vendor identifier
        vendor_name: Vendor name for display
        invoice_number: Unique invoice number from vendor
        invoice_date: Date on the invoice
        due_date: Payment due date
        status: Current invoice status
        subtotal: Invoice subtotal before tax
        tax_amount: Tax amount
        total_amount: Total invoice amount
        currency: ISO currency code
        payment_terms: Payment terms description
        notes: Additional notes
        po_reference: Reference to related purchase order
        matched_by: User/system that performed matching
        matched_at: Timestamp of matching decision
    """

    __tablename__ = "invoices"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(500), nullable=False)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial details
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        InvoiceStatus.as_enum(),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
    )

    # References
    po_reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Matching metadata
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matched_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Additional fields
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_credit_memo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_invoice_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

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
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoice_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoice_status_date", "status", "invoice_date"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice for granular matching.
    """

    __tablename__ = "invoice_lines"

    # Parent reference
    invoice_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line item details
    line_number: Mapped[int] = mapped_column(nullable=False, default=1)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Quantity and pricing
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Matching references
    po_line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Match status
    matched: Mapped[bool] = mapped_column(nullable=False, default=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")

    __table_args__ = (
        Index("ix_invoice_line_sku", "sku"),
        Index("ix_invoice_line_po_ref", "po_line_reference"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description} x{self.quantity}>"
