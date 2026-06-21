# models/purchase_order.py
"""
PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents POs from ERP system for matching against invoices.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

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

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Purchase Order model representing orders sent to vendors.
    
    POs contain line items that invoices should be matched against.
    The matching engine compares invoice lines to PO lines.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_vendor_po_number", "vendor_id", "po_number", unique=True),
        {"schema": None},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Core Fields
    # ─────────────────────────────────────────────────────────────────────────
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor/Supplier identifier from ERP",
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor display name",
    )
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Purchase order number",
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="PO creation date",
    )
    delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Expected/requested delivery date",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Financial Fields
    # ─────────────────────────────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
    )
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
        doc="PO total amount",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────────
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.APPROVED,
        index=True,
        doc="Current PO status",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────────────────
    erp_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="ERP system reference number",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created the PO",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} to {self.vendor_id}>"

    @property
    def total_ordered(self) -> Decimal:
        """Calculate total quantity ordered across all lines."""
        return sum(line.ordered_quantity for line in self.lines)

    @property
    def total_received(self) -> Decimal:
        """Calculate total quantity received across all lines."""
        return sum(line.received_quantity or Decimal("0") for line in self.lines)

    @property
    def balance_remaining(self) -> Decimal:
        """Calculate remaining balance."""
        return self.total_amount - sum(
            line.matched_amount or Decimal("0") for line in self.lines
        )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """
    Purchase Order Line item model.
    
    Represents individual line items on a PO for line-level matching.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_sku", "sku"),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Foreign Keys
    # ─────────────────────────────────────────────────────────────────────────
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Line Details
    # ─────────────────────────────────────────────────────────────────────────
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number on PO",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product/Item SKU",
    )
    ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    received_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        default=Decimal("0"),
        doc="Received quantity",
    )
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure (EA, KG, etc.)",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Pricing
    # ─────────────────────────────────────────────────────────────────────────
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Tax rate as decimal",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Matching/Invoice History
    # ─────────────────────────────────────────────────────────────────────────
    matched_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        default=Decimal("0"),
        doc="Quantity matched/invoiced",
    )
    matched_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        default=Decimal("0"),
        doc="Amount matched/invoiced",
    )
    is_fully_matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether line is fully matched",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"

    @property
    def balance_quantity(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.ordered_quantity - (self.matched_quantity or Decimal("0"))

    @property
    def balance_amount(self) -> Decimal:
        """Calculate remaining amount to be invoiced."""
        return self.line_total - (self.matched_amount or Decimal("0"))

    @property
    def is_over_matched(self) -> bool:
        """Check if matched quantity exceeds ordered quantity."""
        return (self.matched_quantity or Decimal("0")) > self.ordered_quantity
