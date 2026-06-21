# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Represents AP invoices with their line items for matching against
purchase orders and delivery notes.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing AP invoices from suppliers.

    Attributes:
        invoice_number: Unique invoice identifier
        supplier_id: External supplier identifier
        supplier_name: Supplier company name
        invoice_date: Date on the invoice
        due_date: Payment due date
        status: Current invoice status
        subtotal: Sum of line amounts before tax
        tax_amount: Total tax amount
        total_amount: Grand total including tax
        currency: ISO currency code (e.g., USD, EUR)
        notes: Optional notes/comments
        po_reference: Optional PO number reference
        received_at: When the invoice was received/processed
    """

    __tablename__ = "invoices"

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    # Financial amounts (stored as DECIMAL for precision)
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
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # References and metadata
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Audit fields
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
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
        UniqueConstraint("invoice_number", "supplier_id", name="uq_invoice_number_supplier"),
        Index("ix_invoice_supplier_date", "supplier_id", "invoice_date"),
        Index("ix_invoice_status_received", "status", "received_at"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.supplier_name}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Individual line items on an invoice.

    Attributes:
        line_number: Line item sequence number
        description: Item description
        quantity: Invoiced quantity
        unit_price: Price per unit
        line_total: quantity * unit_price
        status: Match status for this line
        matched_amount: Amount matched to PO lines
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )

    # Matching status
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="line_status"),
        nullable=False,
        default=LineStatus.PENDING,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Match confidence score (0-100)
    match_score: Mapped[int | None] = mapped_column(
        nullable=True,
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
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoice_line_invoice_line_num", "invoice_id", "line_number"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if line is fully matched."""
        return self.matched_quantity >= self.quantity

    @property
    def is_partially_matched(self) -> bool:
        """Check if line is partially matched."""
        return Decimal("0") < self.matched_quantity < self.quantity

    @property
    def match_percentage(self) -> Decimal:
        """Calculate match percentage."""
        if self.quantity == 0:
            return Decimal("100") if self.matched_quantity == 0 else Decimal("0")
        return (self.matched_quantity / self.quantity) * Decimal("100")
