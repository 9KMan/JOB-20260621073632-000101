# models/purchase_order.py
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import BaseModel
from models.enums import PurchaseOrderStatus, LineStatus


if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(BaseModel):
    """
    Purchase Order model from ERP.
    
    Attributes:
        po_number: Unique PO number
        vendor_id: Vendor identifier
        vendor_name: Vendor name
        po_date: PO creation date
        delivery_date: Expected delivery date
        subtotal: PO subtotal
        tax_amount: Tax amount
        total_amount: Total PO amount
        currency: Currency code
        status: Current PO status
    """

    __tablename__ = "purchase_orders"

    # Core PO fields
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique PO number from ERP",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name",
    )

    # Dates
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="PO creation date",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )
    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="PO expiry date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="PO subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
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
        default=PurchaseOrderStatus.ACTIVE,
        index=True,
        doc="Current PO status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes",
    )

    # ERP reference
    erp_po_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="PO ID in ERP system",
    )
    department_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Department code",
    )
    cost_center: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Cost center",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_date", "vendor_id", "po_date"),
        Index("ix_purchase_orders_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, number={self.po_number}, status={self.status})>"


class PurchaseOrderLine(BaseModel):
    """
    Purchase Order Line Item model.
    
    Attributes:
        line_number: Line item number
        description: Line description
        quantity: Ordered quantity
        received_quantity: Quantity received so far
        unit_price: Price per unit
        line_total: Total line amount
        status: Line status
    """

    __tablename__ = "purchase_order_lines"

    # Parent reference
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to parent PO",
    )

    # Line details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number",
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Product category",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Ordered quantity",
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Quantity received so far",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Quantity invoiced so far",
    )

    # Amounts
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
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Tax rate",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        index=True,
        doc="Line status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Line-specific notes",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_po_lines_po_line", "purchase_order_id", "line_number"),
        Index("ix_po_lines_sku", "sku"),
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.quantity - self.received_quantity

    @property
    def invoicable_quantity(self) -> Decimal:
        """Calculate quantity that can be invoiced."""
        return min(self.received_quantity, self.quantity) - self.invoiced_quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line={self.line_number}, qty={self.quantity})>"
