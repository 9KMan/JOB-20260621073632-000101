// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNote, DeliveryNoteLine
    from models.invoice import Invoice, InvoiceLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model.

    Represents purchase orders sent to suppliers.

    Attributes:
        id: UUID primary key
        po_number: Unique PO number
        supplier_id: External supplier identifier
        supplier_name: Name of the supplier
        po_date: Date of the PO
        expected_delivery_date: Expected delivery date
        total_amount: Total PO amount
        currency: Currency code (ISO 4217)
        status: Current PO status
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", "supplier_id", name="uq_po_number_supplier"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        {"schema": None},
    )

    # Core fields
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Unique PO number",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="External supplier identifier",
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the supplier",
    )

    # Dates
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date of the PO",
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )
    confirmed_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Confirmed delivery date from supplier",
    )

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        doc="Total PO amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
        doc="Current PO status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )

    # Relations
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        foreign_keys="Invoice.purchase_order_id",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model.

    Represents individual line items on a purchase order.

    Attributes:
        id: UUID primary key
        purchase_order_id: Parent PO reference
        line_number: Line item number
        sku: Product SKU or item code
        description: Item description
        quantity: Ordered quantity
        unit_price: Price per unit
        total_amount: Line total
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
        Index("ix_purchase_order_lines_sku", "sku"),
        {"schema": None},
    )

    # Foreign key
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent purchase order reference",
    )

    # Line item details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number on the PO",
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU or item code",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        doc="Ordered quantity",
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        default=Decimal("0"),
        doc="Total received quantity",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        default=Decimal("0"),
        doc="Total invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=4),
        nullable=False,
        doc="Price per unit",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )

    # Relations
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="purchase_order_line",
        cascade="all, delete-orphan",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="purchase_order_line",
        cascade="all, delete-orphan",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order_line",
        cascade="all, delete-orphan",
    )
