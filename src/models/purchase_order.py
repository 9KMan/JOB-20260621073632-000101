# src/models/purchase_order.py
"""Purchase Order model and related types."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Purchase Order model representing supplier POs.
    
    Attributes:
        id: Unique identifier (UUID)
        po_number: PO number from ERP system
        supplier_id: External supplier identifier
        supplier_name: Supplier's business name
        buyer_id: Internal buyer identifier
        buyer_name: Buyer's name
        po_date: Date PO was created
        expected_delivery_date: Expected delivery date
        currency: ISO currency code
        subtotal: Sum of line amounts
        tax_amount: Total tax amount
        total_amount: Grand total
        status: Current PO status
        payment_terms: Payment terms description
        shipping_terms: Shipping/incoterms
        notes: Additional notes
        metadata: JSON field for additional data
    """
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_supplier_po", "supplier_id", "po_number", unique=True),
    )
    
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
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
    buyer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    buyer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
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
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "sent",
            "confirmed",
            "partially_received",
            "received",
            "closed",
            "cancelled",
            name="po_status",
            create_constraint=True,
        ),
        nullable=False,
        default="draft",
        index=True,
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    shipping_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
    )


class PurchaseOrderLine(UUIDMixin, TimestampMixin, Base):
    """
    Individual line item on a purchase order.
    
    Attributes:
        id: Unique identifier (UUID)
        po_id: Parent purchase order reference
        line_number: Line item sequence number
        description: Line item description
        product_code: Supplier's product/SKU code
        category: Product category
        quantity: Ordered quantity
        received_quantity: Quantity received so far
        unit_of_measure: UOM
        unit_price: Price per unit
        tax_code: Tax classification code
        tax_rate: Tax rate percentage
        line_total: Calculated line total
        required_delivery_date: Required delivery date
        promised_delivery_date: Supplier's promised date
    """
    
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_product_code", "product_code"),
    )
    
    po_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
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
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    required_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    promised_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    delivery_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
    )
