// models/purchase_order.py
"""Purchase Order and PurchaseOrderLine SQLAlchemy models.

This module defines the PurchaseOrder and PurchaseOrderLine database models
for storing PO data from ERP systems.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model representing a PO from ERP.

    Attributes:
        po_number: Unique PO number
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        order_date: Date PO was created
        delivery_date: Expected delivery date
        subtotal: PO subtotal before tax
        tax_amount: Tax amount
        total_amount: Total PO amount
        currency: Currency code (ISO 4217)
        status: Current document status
        department: Department code
        buyer: Buyer name
        notes: Additional notes
        lines: PO line items
        cross_refs: Cross-reference records for matches
        balance_ledgers: Balance ledger entries
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
        UniqueConstraint("po_number", "vendor_id", name="uq_po_number_vendor"),
    )

    # Core fields
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial fields
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
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Reference fields
    external_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Metadata
    department: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    buyer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    terms: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    is_credit_card_po: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line item model.

    Represents individual line items on a purchase order for
    line-level matching with invoices and delivery notes.

    Attributes:
        purchase_order_id: Parent PO foreign key
        line_number: Line item number
        description: Line item description
        quantity: Ordered quantity
        delivered_quantity: Total delivered quantity
        invoiced_quantity: Total invoiced quantity
        unit_of_measure: Unit of measure
        unit_price: Price per unit
        total_price: Line total (quantity * unit_price)
        tax_rate: Tax rate percentage
        sku: Product SKU
        required_date: Date item is required
        match_weight: Weight for learning algorithm
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
        Index("ix_purchase_order_lines_sku", "sku"),
    )

    # Foreign key
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
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
        index=True,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Tax
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Metadata
    required_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    match_weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("1.00"),
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
        foreign_keys="InvoiceLine.po_line_id",
        lazy="selectin",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        lazy="selectin",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet delivered."""
        return self.quantity - self.delivered_quantity

    @property
    def remaining_invoiced_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet invoiced."""
        return self.quantity - self.invoiced_quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.description[:30]}>"
