# models/purchase_order.py
"""Purchase Order model for AP Automation Core Engine."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNote


class PurchaseOrderLineItem(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Line items for a purchase order."""

    __tablename__ = "purchase_order_line_items"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="line_items",
    )
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line_item",
        cascade="all, delete-orphan",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLineItem"]] = relationship(
        "DeliveryNoteLineItem",
        back_populates="po_line_item",
    )

    __table_args__ = (
        Index("ix_purchase_order_line_items_po_id", "purchase_order_id"),
    )


from sqlalchemy import ForeignKey


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Purchase Order model representing POs from ERP systems.
    
    Attributes:
        id: UUID primary key
        po_number: Unique PO number from ERP
        supplier_id: External supplier identifier
        supplier_name: Supplier name
        supplier_tax_id: Supplier tax/VAT identification
        order_date: Date the PO was created
        delivery_date: Expected delivery date
        status: Current PO status
        subtotal: Sum of line amounts before tax
        tax_amount: Total tax amount
        total_amount: Grand total
        currency: Currency code (ISO 4217)
        notes: Additional notes
        metadata: Additional JSON metadata
    """

    __tablename__ = "purchase_orders"

    # Core fields
    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supplier_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dates
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial fields
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        default=PurchaseOrderStatus.ACTIVE,
        nullable=False,
    )

    # Additional info
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(nullable=True)

    # Relationships
    line_items: Mapped[list["PurchaseOrderLineItem"]] = relationship(
        "PurchaseOrderLineItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_order_date", "order_date"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_is_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


# Import at bottom to avoid circular imports
from models.delivery_note import DeliveryNoteLineItem
