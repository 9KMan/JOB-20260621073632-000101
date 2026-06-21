# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents purchase orders from the ERP system with header and line items.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order header model.

    Represents a PO from the ERP system with supplier information,
    dates, and line items.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_supplier_number", "supplier_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
        Index("ix_purchase_orders_deleted_at", "deleted_at"),
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Contact
    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    ship_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Financial totals
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
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Payment terms
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.SUBMITTED,
        index=True,
    )

    # Audit fields
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
    )
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Flags
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency_code}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order line item model.

    Represents individual line items within a purchase order.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_sku", "sku"),
        Index("ix_purchase_order_lines_deleted_at", "deleted_at"),
    )

    # Parent reference
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    barcode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    manufacturer_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Delivery tracking
    promised_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    actual_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description} x {self.quantity_ordered}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def is_fully_received(self) -> bool:
        """Check if PO line is fully received."""
        return self.quantity_received >= self.quantity_ordered

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if PO line is fully invoiced."""
        return self.quantity_invoiced >= self.quantity_ordered


__all__ = [
    "PurchaseOrder",
    "PurchaseOrderLine",
]
