// models/purchase_order.py
"""Purchase order model definition."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Date,
    Numeric,
    Text,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNote
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase order model representing supplier orders.
    
    Attributes:
        id: UUID primary key
        po_number: Unique PO identifier
        supplier_id: External supplier identifier
        supplier_name: Supplier name
        order_date: Date PO was created
        delivery_date: Expected delivery date
        total_amount: Total PO amount
        currency: Currency code
        status: Current PO status
        notes: Additional notes
        erp_reference: External ERP system reference
        is_anchored: Whether PO has been anchored
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
    )
    
    po_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        default=PurchaseOrderStatus.APPROVED,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    erp_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    is_anchored: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Relationships
    matched_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_po",
        foreign_keys="Invoice.matched_po_id",
    )
    line_items: Mapped[list["PurchaseOrderLineItem"]] = relationship(
        "PurchaseOrderLineItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
    )


class PurchaseOrderLineItem(Base, UUIDMixin, TimestampMixin):
    """Line items for purchase orders.
    
    Attributes:
        id: UUID primary key
        po_id: Parent purchase order reference
        line_number: Line item sequence number
        description: Item description
        quantity: Ordered quantity
        unit_price: Price per unit
        amount: Total line amount
        uom: Unit of measure
        tax_code: Tax classification code
        delivery_date: Expected delivery date for this line
    """
    
    __tablename__ = "purchase_order_line_items"
    __table_args__ = (
        Index("ix_po_line_items_po_id", "po_id"),
    )
    
    po_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="line_items",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line_item",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line_item",
    )
