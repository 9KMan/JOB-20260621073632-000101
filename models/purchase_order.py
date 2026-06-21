// models/purchase_order.py
"""Purchase Order and PurchaseOrderLine SQLAlchemy models.

This module defines the database models for purchase orders received
from the ERP system and their line items for matching against invoices.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
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
from models.enums import PurchaseOrderStatus


if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.delivery_note import DeliveryNoteLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase Order model received from ERP.

    Represents a purchase order that will be matched against
    incoming invoices and delivery notes.

    Attributes:
        po_number: Unique PO number from ERP.
        supplier_id: External supplier identifier.
        supplier_name: Supplier name for reference.
        po_date: Date the PO was created.
        delivery_date: Expected delivery date.
        currency: ISO currency code.
        total_amount: Total PO amount.
        status: Current PO status.
        notes: Additional notes.
        metadata: JSON field for additional PO data.

    Relationships:
        lines: One-to-many relationship with PurchaseOrderLine.
        invoices: One-to-many relationship with matched Invoices.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        {"comment": "Purchase orders from ERP for matching"},
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique PO number from ERP",
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
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date the PO was created",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO currency code",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total PO amount",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        doc="Current PO status",
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        type_=Text,
        nullable=True,
        doc="JSON field for additional PO data",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Line items on this PO",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        foreign_keys="Invoice.purchase_order_id",
        lazy="selectin",
        doc="Invoices matched to this PO",
    )

    def __repr__(self) -> str:
        """String representation of the purchase order."""
        return (
            f"<PurchaseOrder(id={self.id}, "
            f"po_number={self.po_number}, "
            f"supplier_id={self.supplier_id}, "
            f"status={self.status.value})>"
        )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line item model.

    Represents individual line items on a purchase order that
    will be matched against invoice lines and delivery note lines.

    Attributes:
        line_number: Line item sequence number.
        description: Line item description.
        product_code: Product/SKU code.
        quantity: Ordered quantity.
        unit_of_measure: Unit of measure.
        unit_price: Price per unit.
        line_total: Total line amount.
        received_quantity: Total quantity received.
        invoiced_quantity: Total quantity invoiced.
        tax_code: Tax classification code.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
        Index("ix_purchase_order_lines_product_code", "product_code"),
        {"comment": "Line items on purchase orders"},
    )

    # Foreign key
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_orders.id",
            ondelete="CASCADE",
            match="FULL",
        ),
        nullable=False,
        doc="Reference to parent purchase order",
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
        doc="Product/SKU code",
    )

    # Quantities and pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
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

    # Tracking quantities
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Total quantity received",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Total quantity invoiced",
    )

    # Tax
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Tax classification code",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        lazy="selectin",
        doc="Parent purchase order",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
        lazy="selectin",
        doc="Invoice lines matched to this PO line",
    )
    delivery_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys="DeliveryNoteLine.po_line_id",
        lazy="selectin",
        doc="Delivery lines matched to this PO line",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet invoiced."""
        return self.quantity - self.invoiced_quantity

    @property
    def pending_delivery_quantity(self) -> Decimal:
        """Calculate quantity pending delivery."""
        return self.quantity - self.received_quantity

    def __repr__(self) -> str:
        """String representation of the PO line."""
        return (
            f"<PurchaseOrderLine(id={self.id}, "
            f"line_number={self.line_number}, "
            f"product_code={self.product_code}, "
            f"quantity={self.quantity})>"
        )
