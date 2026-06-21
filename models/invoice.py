// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

This module defines the database models for invoices and their line items,
which represent the incoming supplier invoices to be matched and processed.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin
from models.enums import InvoiceStatus, MatchingStatus


if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrder


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice model representing a supplier invoice.

    An invoice contains header information and multiple line items
    that will be matched against purchase orders and delivery notes.

    Attributes:
        invoice_number: Unique invoice number from supplier.
        supplier_id: External supplier identifier.
        supplier_name: Supplier name for reference.
        invoice_date: Date on the invoice.
        due_date: Payment due date.
        currency: ISO currency code (e.g., USD, EUR).
        subtotal: Invoice subtotal before tax.
        tax_amount: Total tax amount.
        total_amount: Total invoice amount including tax.
        status: Current invoice status.
        matching_status: Status of the matching process.
        purchase_order_id: Reference to matched purchase order.
        matched_at: Timestamp when invoice was matched.
        decision: Final matching decision type.
        confidence_score: Match confidence score (0.0-1.0).
        notes: Additional notes or comments.
        metadata: JSON field for additional invoice data.

    Relationships:
        lines: One-to-many relationship with InvoiceLine.
        purchase_order: Optional relationship with matched PurchaseOrder.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_matching_status", "matching_status"),
        Index("ix_invoices_purchase_order_id", "purchase_order_id"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        {"comment": "Supplier invoices to be matched against POs"},
    )

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique invoice number from supplier",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="External supplier identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Supplier name for reference",
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date on the invoice",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )

    # Financial amounts (stored as precise decimal)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO currency code",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Invoice subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total invoice amount including tax",
    )

    # Status fields
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50),
        nullable=False,
        default=InvoiceStatus.SUBMITTED,
        doc="Current invoice status",
    )
    matching_status: Mapped[MatchingStatus] = mapped_column(
        String(50),
        nullable=False,
        default=MatchingStatus.PENDING,
        doc="Status of the matching process",
    )

    # Matching references
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_orders.id",
            ondelete="SET NULL",
            match="FULL",
        ),
        nullable=True,
        doc="Reference to matched purchase order",
    )

    # Matching results
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when invoice was matched",
    )
    decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Final matching decision type",
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Match confidence score (0.0-1.0)",
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        type_=Text,  # Will be handled by custom type in production
        nullable=True,
        doc="JSON field for additional invoice data",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Line items on this invoice",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
        foreign_keys=[purchase_order_id],
        lazy="selectin",
        doc="Matched purchase order",
    )

    def __repr__(self) -> str:
        """String representation of the invoice."""
        return (
            f"<Invoice(id={self.id}, "
            f"invoice_number={self.invoice_number}, "
            f"supplier_id={self.supplier_id}, "
            f"status={self.status.value})>"
        )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice that will be
    matched against purchase order lines and delivery note lines.

    Attributes:
        line_number: Line item sequence number.
        description: Line item description.
        product_code: Supplier product/SKU code.
        quantity: Invoiced quantity.
        unit_of_measure: Unit of measure (e.g., EA, KG).
        unit_price: Price per unit.
        line_total: Total line amount (quantity * unit_price).
        tax_code: Tax classification code.
        tax_rate: Tax rate percentage.
        po_line_id: Reference to matched PO line.
        delivery_line_id: Reference to matched delivery line.
        matched_quantity: Quantity that has been matched.
        matched_amount: Amount that has been matched.
        match_confidence: Match confidence level.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_delivery_line_id", "delivery_line_id"),
        Index("ix_invoice_lines_product_code", "product_code"),
        {"comment": "Line items on invoices"},
    )

    # Foreign key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE",
            match="FULL",
        ),
        nullable=False,
        doc="Reference to parent invoice",
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Supplier product/SKU code",
    )

    # Quantities and pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )

    # Tax information
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Tax classification code",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Tax rate percentage",
    )

    # Matching references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_order_lines.id",
            ondelete="SET NULL",
            match="FULL",
        ),
        nullable=True,
        doc="Reference to matched PO line",
    )
    delivery_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "delivery_note_lines.id",
            ondelete="SET NULL",
            match="FULL",
        ),
        nullable=True,
        doc="Reference to matched delivery line",
    )

    # Match results
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity that has been matched",
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Amount that has been matched",
    )
    match_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Match confidence score (0.0-1.0)",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
        lazy="selectin",
        doc="Parent invoice",
    )

    def __repr__(self) -> str:
        """String representation of the invoice line."""
        return (
            f"<InvoiceLine(id={self.id}, "
            f"line_number={self.line_number}, "
            f"product_code={self.product_code}, "
            f"quantity={self.quantity})>"
        )


# Alias for backward compatibility
InvoiceLineItem = InvoiceLine
