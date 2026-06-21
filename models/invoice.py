# models/invoice.py
"""Invoice model for the AP Automation Engine."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus, MatchStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNoteLine
    from models.purchase_order import PurchaseOrderLine


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing supplier invoices.

    Attributes:
        invoice_number: Unique invoice number from supplier
        vendor_id: External vendor identifier
        vendor_name: Supplier name
        invoice_date: Date on the invoice
        due_date: Payment due date
        currency: Currency code (e.g., USD, EUR)
        subtotal: Invoice subtotal before tax
        tax_amount: Tax amount
        total_amount: Total invoice amount
        status: Current document status
        match_status: Current matching status
        matched_at: Timestamp when fully matched
        approved_at: Timestamp when approved
        approved_by: User who approved (if manual)
        notes: Additional notes
        metadata: JSON metadata for extensibility
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_match_status", "match_status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
    )

    # Basic invoice information
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial amounts (stored as Decimal for precision)
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

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.DRAFT,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        String(20),
        nullable=False,
        default=MatchStatus.PENDING,
    )

    # Matching timestamps
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Notes and metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ({self.status.value})>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Attributes:
        invoice_id: Parent invoice reference
        line_number: Line item number
        description: Item description
        quantity: Invoice quantity
        unit_of_measure: UOM
        unit_price: Price per unit
        total_price: Line total (quantity * unit_price)
        matched_quantity: Quantity matched to PO/delivery
        status: Line status
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Prices
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Tax
    tax_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="invoice_delivery_note_links",
        back_populates="invoice_lines",
        lazy="selectin",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"

    @property
    def match_percentage(self) -> Decimal:
        """Calculate match percentage for this line."""
        if self.quantity == 0:
            return Decimal("0")
        return (self.matched_quantity / self.quantity) * Decimal("100")
