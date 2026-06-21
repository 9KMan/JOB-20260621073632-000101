# models/purchase_order.py
"""Purchase Order model for the AP Automation Engine."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNoteLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model from ERP system.

    Attributes:
        po_number: Unique PO number from ERP
        vendor_id: External vendor identifier
        vendor_name: Supplier name
        po_date: PO creation date
        delivery_date: Expected delivery date
        expiration_date: PO expiration date
        currency: Currency code
        subtotal: PO subtotal
        tax_amount: Tax amount
        total_amount: Total PO amount
        status: Current document status
        department: Requesting department
        buyer: Buyer name
        notes: Additional notes
        metadata: JSON metadata for extensibility
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_created_at", "created_at"),
    )

    # Basic PO information
    po_number: Mapped[str] = mapped_column(
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
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial amounts
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
        default=DocumentStatus.PENDING,
    )

    # Additional fields
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    buyer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} ({self.status.value})>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order line item model.

    Attributes:
        purchase_order_id: Parent PO reference
        line_number: Line item number
        description: Item description
        sku: Supplier SKU
        quantity: Ordered quantity
        delivered_quantity: Quantity already delivered
        remaining_quantity: Quantity not yet delivered
        unit_of_measure: UOM
        unit_price: Price per unit
        total_price: Line total
        tax_rate: Tax rate percentage
        tax_amount: Tax amount
        status: Line status
        required_date: Required delivery date
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_sku", "sku"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
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

    # Required date
    required_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="po_delivery_note_links",
        back_populates="po_lines",
        lazy="selectin",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"

    def update_remaining_quantity(self) -> None:
        """Update remaining quantity based on delivered quantity."""
        self.remaining_quantity = self.quantity - self.delivered_quantity
