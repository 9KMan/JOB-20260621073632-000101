# src/models/purchase_order.py
"""Purchase Order model for AP Automation Core Engine.

Represents purchase orders from the ERP system that invoices
need to be matched against.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrderLine(TimestampMixin, UUIDMixin, Base):
    """Individual line item on a purchase order.

    Each PO can have multiple line items that represent ordered goods/services.
    """

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to parent purchase order",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity received so far",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity invoiced so far",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure (e.g., EA, KG, M)",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Tax amount for this line",
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        doc="Line status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes for this line",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        foreign_keys=[purchase_order_id],
    )

    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
        Index("ix_purchase_order_lines_status", "status"),
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining uninvoiced quantity."""
        return self.quantity - self.invoiced_quantity

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.invoiced_quantity >= self.quantity


class PurchaseOrder(TimestampMixin, SoftDeleteMixin, UUIDMixin, Base):
    """Purchase Order model representing orders from ERP.

    Contains header information and line items for matching against
    invoices and delivery notes.
    """

    __tablename__ = "purchase_orders"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Vendor/supplier identifier from ERP",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor/supplier name",
    )
    vendor_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Vendor tax identification number",
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Purchase order number",
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date PO was created",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Requested delivery date",
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were received",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="PO subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Total tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="PO total (subtotal + tax)",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="approved",
        doc="PO status",
    )

    # ERP reference
    erp_po_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="PO ID in the ERP system",
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
        doc="Source system identifier",
    )

    # Approval information
    approved_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User who approved the PO",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when approved",
    )

    # Additional metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )
    ship_to: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Ship-to address",
    )
    bill_to: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Bill-to address",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_erp_po_id", "erp_po_id"),
        Index("ix_purchase_orders_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} from {self.vendor_name}>"

    @property
    def total_invoiced(self) -> Decimal:
        """Calculate total amount invoiced against this PO."""
        return sum(line.invoiced_quantity * line.unit_price for line in self.lines)

    @property
    def remaining_balance(self) -> Decimal:
        """Calculate remaining balance for this PO."""
        return self.total_amount - self.total_invoiced
