# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import InvoiceStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote, DeliveryNoteLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model.

    Represents an incoming invoice that needs to be matched against
    purchase orders and delivery notes.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_po_id", "po_id"),
        Index("ix_invoices_created_at", "created_at"),
        {"schema": None},
    )

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Reference to PO
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Invoice dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financials
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
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status tracking
    status: Mapped[InvoiceStatus] = mapped_column(
        String(30),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )

    # Matching results
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Exception tracking
    has_exceptions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    exception_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Approval tracking
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Metadata
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    raw_data: Mapped[dict | None] = mapped_column(
        nullable=True,
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
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="invoice_delivery_note_lines",
        back_populates="invoice_lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.vendor_number}>"

    @property
    def is_matched(self) -> bool:
        """Check if invoice has been matched."""
        return self.match_score is not None

    @property
    def is_approved(self) -> bool:
        """Check if invoice has been approved."""
        return self.approved_at is not None


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_status", "status"),
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line_number"),
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
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product identification
    product_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
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
        default=Decimal("0"),
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LineStatus.OPEN,
        index=True,
    )

    # PO Line reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Delivery Note Line references
    delivery_note_line_ids: Mapped[list[uuid.UUID]] = mapped_column(
        nullable=True,
    )

    # Matching results
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
        lazy="selectin",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
        lazy="selectin",
    )
    balance_ledger: Mapped["BalanceLedger | None"] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if line is fully matched."""
        return self.matched_quantity >= self.quantity_invoiced

    @property
    def match_percentage(self) -> float:
        """Calculate match percentage."""
        if self.quantity_invoiced == 0:
            return 0.0
        return float(self.matched_quantity / self.quantity_invoiced)
