# models/purchase_order.py
# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import PurchaseOrderStatus


class PurchaseOrder(Base, TimestampMixin):
    """Purchase order header model.

    Represents a PO document created in the ERP system.
    Contains header-level information and references to PO lines.
    """

    __tablename__ = "purchase_orders"

    # Document identification
    po_number: Mapped[str] = mapped_column(
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

    # Financial amounts
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

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        default=PurchaseOrderStatus.SUBMITTED,
        nullable=False,
        index=True,
    )

    # Dates
    po_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
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
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        lazy="selectin",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"

    @property
    def total_ordered_quantity(self) -> Decimal:
        """Calculate total ordered quantity across all lines."""
        return sum(line.quantity for line in self.lines)

    @property
    def total_invoiced_quantity(self) -> Decimal:
        """Calculate total invoiced quantity across all lines."""
        return sum(line.total_invoiced_quantity for line in self.lines)


class PurchaseOrderLine(Base, TimestampMixin):
    """Purchase order line item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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

    # Delivered and invoiced tracking
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        lazy="selectin",
    )
    delivery_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_po_lines_po_id", "purchase_order_id"),
        Index("ix_po_lines_product_code", "product_code"),
        Index("ix_po_lines_line_number", "purchase_order_id", "line_number", unique=True),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining undelivered quantity."""
        return max(Decimal("0.0000"), self.quantity - self.delivered_quantity)

    @property
    def total_invoiced_quantity(self) -> Decimal:
        """Calculate total invoiced quantity."""
        return sum(il.matched_quantity for il in self.invoice_lines)

    @property
    def delivery_percentage(self) -> float:
        """Calculate delivery percentage."""
        if self.quantity == 0:
            return 0.0
        return float(self.delivered_quantity / self.quantity * 100)

    @property
    def invoice_percentage(self) -> float:
        """Calculate invoice percentage."""
        if self.quantity == 0:
            return 0.0
        return float(self.invoiced_quantity / self.quantity * 100)
