# models/purchase_order.py
"""Purchase Order and PurchaseOrderLine SQLAlchemy models."""

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.delivery_note import DeliveryNoteLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Purchase Order header model.
    
    Represents a PO created in the ERP system.
    """
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
    )
    
    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # PO Identification
    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Financial Summary
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.ACTIVE,
    )
    
    # Source Information
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="erp")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Terms
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Additional Fields
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ship_to: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bill_to: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Purchase Order Line Item model.
    
    Represents individual line items on a PO.
    """
    
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "po_id", "line_number", unique=True),
        Index("ix_purchase_order_lines_sku", "sku"),
    )
    
    # Parent Purchase Order
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Line Information
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Product Information
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    
    # Remaining Balances
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
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
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
