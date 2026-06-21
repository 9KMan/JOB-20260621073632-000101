# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

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
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, BaseMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrderLine


class Invoice(Base, BaseMixin):
    """Invoice model representing a supplier invoice."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
        UniqueConstraint("vendor_id", "invoice_number", name="uq_invoices_vendor_invoice"),
    )

    # Vendor Information
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

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial Information
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

    # Status and Matching
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
    )
    matched_po_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    match_confidence: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    match_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Exception Information
    has_exception: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    exception_types: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Approval Information
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # External References
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    erp_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Additional Data
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
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


class InvoiceLine(Base, BaseMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
    )

    # Parent Invoice
    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product Information
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantity
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
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
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
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

    # Matching
    po_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Line Status
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_exception: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    exception_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.id} line={self.line_number} amount={self.line_amount}>"
