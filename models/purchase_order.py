# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents purchase orders from the ERP system for invoice matching.
"""

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase order model representing orders sent to vendors.

    Attributes:
        po_number: Unique PO number
        vendor_id: Vendor identifier
        vendor_name: Vendor name
        order_date: Date PO was created
        delivery_date: Expected delivery date
        status: PO status
        total_amount: Total PO amount
        currency: ISO currency code
    """

    __tablename__ = "purchase_orders"

    # PO identification
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(500), nullable=False)
    vendor_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dates
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        PurchaseOrderStatus.as_enum(),
        nullable=False,
        default=PurchaseOrderStatus.PENDING,
        index=True,
    )

    # Additional
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms: Mapped[str | None] = mapped_column(String(200), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_po_vendor_date", "vendor_id", "order_date"),
        Index("ix_po_status_date", "status", "order_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase order line item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"

    # Parent reference
    purchase_order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line item details
    line_number: Mapped[int] = mapped_column(nullable=False, default=1)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantity and pricing
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Delivery tracking
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_po_line_sku", "sku"),
        Index("ix_po_line_po", "purchase_order_id", "line_number"),
    )

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.quantity_ordered - self.quantity_delivered

    @property
    def quantity_pending_invoice(self) -> Decimal:
        """Calculate quantity pending invoice."""
        return self.quantity_delivered - self.quantity_invoiced

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"
