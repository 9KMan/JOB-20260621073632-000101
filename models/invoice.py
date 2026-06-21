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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CompanyMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import CurrencyCode, InvoiceStatus, LineType, TaxType

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyMixin):
    """Invoice database model.

    Represents an incoming invoice from a supplier for processing and matching
    against purchase orders and delivery notes.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "company_code", name="uq_invoice_number_company"),
        Index("ix_invoices_supplier_code", "supplier_code"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_received_at", "received_at"),
        Index("ix_invoices_supplier_invoice_number", "supplier_invoice_number"),
        {"schema": None},
    )

    # Reference fields
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Date fields
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
    )

    # Financial fields
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
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    balance_due: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Status and matching
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=InvoiceStatus.RECEIVED.value,
        index=True,
    )
    match_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    decision_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Metadata
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_credit_note: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"

    @property
    def is_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.balance_due <= 0

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.due_date is None:
            return False
        return date.today() > self.due_date and not self.is_paid


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Invoice line item database model.

    Represents individual line items on an invoice for line-level matching.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
        {"schema": None},
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    external_line_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Product/Service identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    line_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=LineType.STANDARD.value,
    )

    # Quantity
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Tax
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Matching
    match_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_delivery_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"

    @property
    def is_tax_line(self) -> bool:
        """Check if this is a tax line."""
        return self.line_type == LineType.TAX.value

    @property
    def is_discount_line(self) -> bool:
        """Check if this is a discount line."""
        return self.line_type == LineType.DISCOUNT.value
