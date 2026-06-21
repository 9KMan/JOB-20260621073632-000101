# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin


class Invoice(Base, TimestampMixin, SoftDeleteMixin):
    """Invoice header model.

    Represents an invoice document received from a vendor.
    Contains header-level information and references to invoice lines.
    """

    __tablename__ = "invoices"

    # Document identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Financial amounts (stored as Decimal for precision)
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
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Dates
    invoice_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Reference to PO
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Matching results
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    match_percentage: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
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
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_po_id", "purchase_order_id"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice.
    Each line can be matched against PO lines and delivery note lines.
    """

    __tablename__ = "invoice_lines"

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
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product/supplier references
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Match references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Matching results
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    match_percentage: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    delivery_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_product_code", "product_code"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"
