// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Purchase orders are documents created to request goods/services from vendors.
Each PO can have multiple line items.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import PurchaseOrderStatus, LineStatus


class PurchaseOrder(Base):
    """Purchase Order model.

    Represents a purchase order created to request goods or services.

    Attributes:
        id: UUID primary key
        po_number: Unique PO number
        vendor_id: External vendor identifier
        vendor_name: Vendor name for display
        order_date: Date PO was created
        expected_delivery_date: Expected delivery date
        status: PO status
        subtotal: PO subtotal
        tax_amount: Tax amount
        total_amount: Total PO amount
        currency: Currency code
        lines: Associated line items
    """

    __tablename__ = "purchase_orders"

    # Document identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial
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
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # References
    external_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    department_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    cost_center: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Approval
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Additional data
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    shipping_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    billing_address: Mapped[Optional[str]] = mapped_column(
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
        Index("ix_po_vendor_date", "vendor_id", "order_date"),
        Index("ix_po_status_date", "status", "order_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


class PurchaseOrderLine(Base):
    """Purchase Order Line Item model.

    Represents individual line items on a purchase order.

    Attributes:
        id: UUID primary key
        purchase_order_id: Parent PO reference
        line_number: Line sequence number
        description: Item description
        quantity: Ordered quantity
        delivered_quantity: Total delivered quantity
        invoiced_quantity: Total invoiced quantity
        unit_price: Price per unit
        total_amount: Line total
        sku: Product/Item SKU
        uom: Unit of measure
    """

    __tablename__ = "purchase_order_lines"

    # Parent reference
    purchase_order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
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

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Product reference
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    uom: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        default=LineStatus.OPEN,
        nullable=False,
        index=True,
    )

    # Delivery tracking
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Additional data
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_po_line",
        lazy="selectin",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_po_line",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_po_line_po", "purchase_order_id", "line_number"),
        Index("ix_po_line_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to deliver."""
        return self.quantity - self.delivered_quantity

    @property
    def remaining_invoice_quantity(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.quantity - self.invoiced_quantity
