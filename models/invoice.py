# models/invoice.py
"""Invoice model for AP Automation Core Engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus


if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class InvoiceLineItem(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Line items for an invoice."""

    __tablename__ = "invoice_line_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0"))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    po_line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    matched_balance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledger.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="line_items",
    )
    balance_ledger: Mapped["BalanceLedger | None"] = relationship(
        "BalanceLedger",
        back_populates="invoice_line_items",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice_line_item",
        foreign_keys="CrossRef.invoice_line_item_id",
    )

    __table_args__ = (
        Index("ix_invoice_line_items_invoice_id", "invoice_id"),
        Index("ix_invoice_line_items_matched_balance_id", "matched_balance_id"),
    )


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Invoice model representing supplier invoices.
    
    Attributes:
        id: UUID primary key
        invoice_number: Unique invoice number
        supplier_id: External supplier identifier
        supplier_name: Supplier name
        supplier_tax_id: Supplier tax/VAT identification
        invoice_date: Date of the invoice
        due_date: Payment due date
        status: Current invoice status
        subtotal: Sum of line amounts before tax
        tax_amount: Total tax amount
        total_amount: Grand total (subtotal + tax)
        currency: Currency code (ISO 4217)
        notes: Additional notes or comments
        payment_reference: Payment reference when paid
        paid_date: Date payment was made
    """

    __tablename__ = "invoices"

    # Core fields
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supplier_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dates
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())

    # Financial fields
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Status
    status: Mapped[InvoiceStatus] = mapped_column(
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )

    # Matching fields
    matching_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Payment fields
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Additional info
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(nullable=True)

    # Relationships
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        "InvoiceLineItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_due_date", "due_date"),
        Index("ix_invoices_is_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"
