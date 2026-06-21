# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Represents AP invoices and their line items.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DecisionType, InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrderLine


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing AP invoices from vendors.

    Attributes:
        invoice_number: Unique invoice identifier
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        invoice_date: Date on invoice
        due_date: Payment due date
        currency: ISO currency code (e.g., USD, EUR)
        subtotal: Invoice subtotal before tax
        tax_amount: Tax amount
        total_amount: Total invoice amount
        status: Current invoice status
        decision_type: Matching decision made
        match_score: Confidence score (0-1)
        matched_po_id: Reference to matched PO if any
        notes: Additional notes
        metadata: Additional JSON metadata
    """

    __tablename__ = "invoices"

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
        String(50),
        nullable=False,
        default=InvoiceStatus.DRAFT.value,
        index=True,
    )
    decision_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_date", "status", "invoice_date"),
        UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_vendor"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice.
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
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
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("1"),
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    matched_pol_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number"),
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"
