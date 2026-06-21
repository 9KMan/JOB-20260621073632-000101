// models/invoice.py
"""Invoice model for the AP Automation Engine."""

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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CustomMixin, SoftDeleteMixin
from models.enums import DocumentStatus, MatchStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote
    from models.purchase_order import PurchaseOrder


class Invoice(Base, CustomMixin, SoftDeleteMixin):
    """Invoice model representing AP invoices.

    Attributes:
        invoice_number: Unique invoice number from vendor.
        vendor_id: External vendor identifier.
        vendor_name: Vendor name for display.
        invoice_date: Date on the invoice.
        due_date: Payment due date.
        status: Current document status.
        match_status: Current matching status.
        subtotal: Pre-tax invoice amount.
        tax_amount: Tax amount.
        total_amount: Total invoice amount (subtotal + tax).
        currency: ISO currency code.
        payment_terms: Payment terms description.
        description: Invoice description.
        reference: External reference number.
        is_credit_memo: Whether this is a credit memo.
        is_paid: Whether the invoice has been paid.
        paid_date: Date invoice was paid.
        approved_by: User who approved the invoice.
        approved_at: Timestamp of approval.
        matched_at: Timestamp of matching completion.
        created_by: User who created the record.
        notes: Additional notes.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("vendor_id", "invoice_number", name="uq_invoice_vendor_number"),
        Index("ix_invoice_vendor_id", "vendor_id"),
        Index("ix_invoice_status", "status"),
        Index("ix_invoice_match_status", "match_status"),
        Index("ix_invoice_invoice_date", "invoice_date"),
        Index("ix_invoice_created_at", "created_at"),
        {"schema": None},
    )

    # Core invoice fields
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
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Status fields
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        String(20),
        default=MatchStatus.PENDING,
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

    # Additional fields
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_credit_memo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    paid_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Approval and matching
    approved_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Audit fields
    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        foreign_keys="CrossRef.invoice_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base, CustomMixin):
    """Invoice line item model.

    Attributes:
        invoice_id: Parent invoice ID.
        line_number: Line item number.
        description: Line description.
        quantity: Invoice quantity.
        unit_price: Price per unit.
        amount: Total line amount.
        tax_code: Tax classification code.
        po_line_id: Reference to matched PO line (optional).
        delivery_note_line_id: Reference to matched DN line (optional).
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_line_invoice_id", "invoice_id"),
        {"schema": None},
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Matching references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="invoice_lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.amount}>"
