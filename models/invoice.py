# models/invoice.py
"""Invoice model definition."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNote
    from models.purchase_order import PurchaseOrder


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Invoice model representing supplier invoices.

    Attributes:
        id: UUID primary key
        invoice_number: Unique invoice number from supplier
        vendor_id: Supplier/vendor identifier
        vendor_name: Supplier name
        vendor_tax_id: Supplier tax identification number
        invoice_date: Date on the invoice
        due_date: Payment due date
        gross_amount: Total invoice amount including tax
        net_amount: Invoice amount excluding tax
        tax_amount: Tax amount
        currency: ISO 4217 currency code (e.g., USD, EUR)
        status: Current invoice status
        po_reference: Reference to linked purchase order
        matching_score: Match confidence score (0-100)
        matching_decision: Automated matching decision
        payment_reference: Payment reference when paid
        notes: Additional notes or comments
        metadata: Additional flexible fields as JSONB
        lines: Child invoice lines
    """

    __tablename__ = "invoices"

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
    vendor_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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

    # Amounts (using Decimal for financial precision)
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status and matching
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50),
        nullable=False,
        default=InvoiceStatus.RECEIVED,
        index=True,
    )
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Matching results
    matching_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Payment
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Tenant support
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Relationships
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
        foreign_keys=[matched_po_id],
    )

    __table_args__ = (
        # Composite indexes for common queries
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_date", "status", "invoice_date"),
        Index("ix_invoices_tenant_status", "tenant_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.vendor_name} - {self.gross_amount} {self.currency}>"

    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining unpaid amount."""
        return self.gross_amount - self.paid_amount

    @property
    def is_fully_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.paid_amount >= self.gross_amount

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.due_date is None:
            return False
        from datetime import date

        return date.today() > self.due_date and not self.is_fully_paid


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual line items on an invoice.

    Attributes:
        id: UUID primary key
        invoice_id: Parent invoice reference
        line_number: Line item number
        description: Line item description
        quantity: Invoiced quantity
        unit_of_measure: UOM
        unit_price: Price per unit
        net_amount: Line net amount
        tax_amount: Line tax amount
        po_line_reference: Reference to matched PO line
        matched_dn_line_id: Reference to matched delivery note line
        matched_quantity: Quantity matched
        status: Line matching status
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Quantity
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Matching
    po_line_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.00"),
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description} x {self.quantity}>"

    @property
    def unmatched_quantity(self) -> Decimal:
        """Calculate unmatched quantity."""
        return self.quantity - self.matched_quantity

    @property
    def match_percentage(self) -> float:
        """Calculate match percentage."""
        if self.quantity == 0:
            return 100.0
        return float((self.matched_quantity / self.quantity) * 100)
