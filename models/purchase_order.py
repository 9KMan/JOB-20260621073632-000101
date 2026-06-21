// models/purchase_order.py
"""Purchase Order and POLine SQLAlchemy models.

This module defines the purchase order data model. POs are received
from ERP systems and serve as the anchor for invoice matching.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import PurchaseOrderStatus, LineStatus

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base):
    """Purchase Order model.
    
    Represents a purchase order received from the ERP system.
    POs serve as the primary anchor for invoice matching.
    
    Attributes:
        id: UUID primary key
        po_number: Unique PO number
        vendor_code: Vendor code
        vendor_name: Vendor name
        order_date: PO order date
        delivery_date: Expected delivery date
        subtotal: PO subtotal
        tax_amount: Tax amount
        total_amount: Total amount
        currency: Currency code
        status: PO status
        notes: Optional notes
        is_credit_note: Whether this is a credit PO
        received_date: When goods were received
        metadata: Additional JSON metadata
        lines: Related PO lines
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_vendor_code", "vendor_code"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
        Index("ix_purchase_orders_created_at", "created_at"),
        UniqueConstraint("po_number", name="uq_po_number"),
    )

    # Primary identifiers
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Unique PO number",
    )
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Vendor code",
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor name",
    )
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Vendor tax ID",
    )

    # Dates
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="PO order date",
    )
    delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Expected delivery date",
    )
    received_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Goods receipt date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Subtotal before tax",
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
        doc="Total amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="po_status"),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        doc="PO status",
    )
    is_credit_note: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this is a credit PO",
    )

    # Additional data
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional JSON metadata",
    )

    # Relationships
    lines: Mapped[List["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} vendor={self.vendor_code} status={self.status.value}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "po_number": self.po_number,
            "vendor_code": self.vendor_code,
            "vendor_name": self.vendor_name,
            "vendor_tax_id": self.vendor_tax_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "received_date": self.received_date.isoformat() if self.received_date else None,
            "subtotal": str(self.subtotal),
            "tax_amount": str(self.tax_amount),
            "total_amount": str(self.total_amount),
            "currency": self.currency,
            "status": self.status.value,
            "is_credit_note": self.is_credit_note,
            "notes": self.notes,
            "lines": [line.to_dict() for line in self.lines],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class POLine(Base):
    """Purchase Order Line model.
    
    Represents individual line items on a purchase order.
    Each line can be matched to invoice lines and delivery note lines.
    
    Attributes:
        id: UUID primary key
        purchase_order_id: Parent PO ID
        line_number: Line item number
        description: Line description
        quantity: Ordered quantity
        unit_of_measure: UOM code
        unit_price: Unit price
        line_amount: Total line amount
        currency: Currency code
        status: Line status
        scheduled_date: Scheduled delivery date
        received_quantity: Quantity received
        invoiced_quantity: Quantity invoiced
        open_quantity: Remaining quantity to receive
        metadata: Additional JSON metadata
    """

    __tablename__ = "po_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "purchase_order_id"),
        Index("ix_po_lines_line_number", "line_number"),
        Index("ix_po_lines_status", "status"),
        Index("ix_po_lines_sku", "sku"),
        UniqueConstraint("purchase_order_id", "line_number", name="uq_po_line_number"),
    )

    # Parent reference
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent PO ID",
    )

    # Line identifiers
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line description",
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Product SKU",
    )
    gtin: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Global Trade Item Number",
    )

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="EA",
        doc="Unit of measure",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="po_line_status"),
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line status",
    )
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Scheduled delivery date",
    )

    # Balance tracking
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity received",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity invoiced",
    )
    open_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Open quantity to receive",
    )

    # Additional data
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional JSON metadata",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
    )
    delivery_note_lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys="DeliveryNoteLine.po_line_id",
    )
    cross_refs: Mapped[List["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="po_line",
    )
    balance_ledger: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
    )

    def __repr__(self) -> str:
        return f"<POLine {self.line_number} qty={self.quantity} open={self.open_quantity}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "purchase_order_id": str(self.purchase_order_id),
            "line_number": self.line_number,
            "description": self.description,
            "sku": self.sku,
            "gtin": self.gtin,
            "quantity": str(self.quantity),
            "unit_of_measure": self.unit_of_measure,
            "unit_price": str(self.unit_price),
            "line_amount": str(self.line_amount),
            "currency": self.currency,
            "status": self.status.value if self.status else None,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "received_quantity": str(self.received_quantity),
            "invoiced_quantity": str(self.invoiced_quantity),
            "open_quantity": str(self.open_quantity),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_fully_received(self) -> bool:
        """Check if line is fully received."""
        return self.received_quantity >= self.quantity

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.invoiced_quantity >= self.quantity

    @property
    def remaining_balance(self) -> Decimal:
        """Get remaining quantity to invoice."""
        return max(Decimal("0"), self.received_quantity - self.invoiced_quantity)

    def update_balances(self, invoiced_qty: Decimal = Decimal("0")) -> None:
        """Update balance quantities.
        
        Args:
            invoiced_qty: Quantity being invoiced.
        """
        self.invoiced_quantity += invoiced_qty
        self.open_quantity = max(Decimal("0"), self.quantity - self.received_quantity)
