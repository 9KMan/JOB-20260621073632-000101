# models/purchase_order.py
# Purchase order table and SQLAlchemy model
# AP Automation Core Engine — FinaRo

"""PurchaseOrder and PurchaseOrderLine SQLAlchemy ORM models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
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

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import (
    PurchaseOrderStatus,
    PurchaseOrderStatusType,
    LineStatus,
    LineStatusType,
)

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.delivery_note import DeliveryNoteLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order model representing a PO from the ERP system.

    Attributes:
        id: UUID primary key.
        po_number: Unique PO number.
        vendor_id: External vendor/system identifier.
        vendor_name: Vendor name for display purposes.
        vendor_address: Vendor address (optional).
        order_date: Date the PO was created.
        delivery_date: Expected delivery date.
        status: Current PO status.
        subtotal: PO subtotal before tax.
        tax_amount: Tax amount.
        total_amount: Total PO amount.
        currency: Currency code (e.g., USD, EUR).
        notes: Additional notes.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
        deleted_at: Soft delete timestamp.
    """

    __tablename__ = "purchase_orders"

    # Basic PO info
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique PO number",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="External vendor/system identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name for display",
    )
    vendor_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Vendor address",
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date the PO was created",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
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
        index=True,
        doc="Total PO amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        PurchaseOrderStatusType,
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
        doc="Current PO status",
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    is_edi: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this PO came via EDI",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="PO line items",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_date", "vendor_id", "order_date"),
        Index("ix_purchase_orders_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase order line item model.

    Attributes:
        id: UUID primary key.
        po_id: Parent PO UUID.
        line_number: Line item number.
        description: Item description.
        quantity: Ordered quantity.
        received_quantity: Quantity received so far.
        invoiced_quantity: Quantity invoiced so far.
        unit_price: Price per unit.
        total_amount: Line total (quantity * unit_price).
        uom: Unit of measure.
        status: Line status.
        delivery_expected_date: Expected delivery date for this line.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "purchase_order_lines"

    # Foreign key
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent PO UUID",
    )

    # Line info
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity received so far",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity invoiced so far",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    uom: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        LineStatusType,
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line status",
    )
    delivery_expected_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date for this line",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        doc="Parent PO",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet received."""
        return self.quantity - self.received_quantity

    @property
    def remaining_invoicable(self) -> Decimal:
        """Calculate remaining quantity that can be invoiced."""
        return self.received_quantity - self.invoiced_quantity

    __table_args__ = (
        Index("ix_purchase_order_lines_po_line", "po_id", "line_number", unique=True),
        Index("ix_purchase_order_lines_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.description[:30]}>"
