# models/purchase_order.py
"""
PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents purchase orders from the ERP system that will be
used as the anchor for invoice matching.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base):
    """
    Purchase Order header model.
    
    Represents a PO from the ERP system that serves as
    the anchor document for invoice matching.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_pos_supplier_number", "supplier_number"),
        Index("ix_pos_po_number", "po_number"),
        Index("ix_pos_status", "status"),
        Index("ix_pos_order_date", "order_date"),
        Index("ix_pos_created_at", "created_at"),
        UniqueConstraint("supplier_number", "po_number", name="uq_po_supplier_number"),
        {"schema": None},
    )

    # PO identification
    supplier_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Supplier/Vendor ID in the ERP system",
    )

    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Supplier/Vendor number",
    )

    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Supplier/Vendor name",
    )

    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Purchase Order number",
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="PO order date",
    )

    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Expected delivery date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="PO subtotal",
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Tax amount",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Total PO amount",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.SUBMITTED,
        index=True,
        comment="Current PO status",
    )

    # Matching tracking
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Total amount invoiced against this PO",
    )

    delivered_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Total amount delivered (from DNs)",
    )

    # Source system
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Source ERP system identifier",
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Original reference in source system",
    )

    # Terms and conditions
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Payment terms code",
    )

    delivery_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Delivery address",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes",
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional metadata as JSON",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        foreign_keys="CrossRef.purchase_order_id",
        cascade="all, delete-orphan",
    )

    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} from {self.supplier_number}>"

    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining PO amount."""
        return self.total_amount - self.invoiced_amount

    @property
    def is_closed(self) -> bool:
        """Check if PO is closed."""
        return self.status in (
            PurchaseOrderStatus.CLOSED,
            PurchaseOrderStatus.COMPLETED,
        )


class PurchaseOrderLine(Base):
    """
    Purchase Order line item model.
    
    Represents individual line items on a PO that can be
    matched against invoice and delivery note lines.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_line_number", "line_number"),
        Index("ix_po_lines_product_code", "product_code"),
        {"schema": None},
    )

    # Parent reference
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Line item number on the PO",
    )

    # Product information
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product/SKU code",
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Line item description",
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Ordered quantity",
    )

    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure (EA, KG, etc.)",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Unit price",
    )

    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Line total (quantity * unit_price)",
    )

    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Tax code",
    )

    # Delivery tracking
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity delivered",
    )

    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity invoiced",
    )

    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Amount invoiced",
    )

    # Relationship
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.product_code} x {self.quantity}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to deliver."""
        return self.quantity - self.delivered_quantity

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.quantity - self.invoiced_quantity

    @property
    def delivery_percentage(self) -> float:
        """Calculate delivery percentage."""
        if self.quantity == 0:
            return 100.0
        return float((self.delivered_quantity / self.quantity) * 100)

    @property
    def invoiced_percentage(self) -> float:
        """Calculate invoiced percentage."""
        if self.quantity == 0:
            return 100.0
        return float((self.invoiced_quantity / self.quantity) * 100)
