# models/purchase_order.py
"""Purchase Order model definition."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Purchase Order model representing supplier POs.

    Attributes:
        id: UUID primary key
        po_number: Unique PO number
        vendor_id: Supplier/vendor identifier
        vendor_name: Supplier name
        vendor_address: Supplier address
        order_date: PO creation date
        delivery_date: Expected delivery date
        gross_amount: Total PO amount including tax
        net_amount: PO amount excluding tax
        tax_amount: Tax amount
        currency: ISO 4217 currency code
        status: Current PO status
        received_amount: Total received amount
        notes: Additional notes
        metadata: Additional flexible fields
        lines: Child PO lines
        matched_invoices: Related matched invoices
    """

    __tablename__ = "purchase_orders"

    # Core PO fields
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
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
    vendor_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    vendor_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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

    # Amounts
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    received_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.OPEN,
        index=True,
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_po",
        foreign_keys="Invoice.matched_po_id",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_date", "vendor_id", "order_date"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_tenant", "tenant_id"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.vendor_name} - {self.gross_amount} {self.currency}>"

    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining unreceived amount."""
        return self.gross_amount - self.received_amount

    @property
    def received_percentage(self) -> float:
        """Calculate received percentage."""
        if self.gross_amount == 0:
            return 0.0
        return float((self.received_amount / self.gross_amount) * 100)

    @property
    def is_fully_received(self) -> bool:
        """Check if PO is fully received."""
        return self.received_amount >= self.gross_amount

    @property
    def is_overdue(self) -> bool:
        """Check if PO delivery is overdue."""
        if self.delivery_date is None:
            return False
        return date.today() > self.delivery_date and not self.is_fully_received


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual line items on a Purchase Order.

    Attributes:
        id: UUID primary key
        po_id: Parent PO reference
        line_number: Line item number
        description: Line item description
        quantity: Ordered quantity
        unit_of_measure: UOM
        unit_price: Price per unit
        net_amount: Line net amount
        tax_amount: Line tax amount
        received_quantity: Quantity already received
        delivered_quantity: Quantity delivered
        invoiced_quantity: Quantity invoiced
        status: Line status
    """

    __tablename__ = "purchase_order_lines"

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Quantity
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Tracking quantities
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.00"),
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.00"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.00"),
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
    )

    __table_args__ = (
        Index("ix_po_lines_po_line", "po_id", "line_number"),
        Index("ix_po_lines_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description} x {self.quantity}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining unreceived quantity."""
        return self.quantity - self.received_quantity

    @property
    def remaining_to_deliver(self) -> Decimal:
        """Calculate remaining to deliver."""
        return self.quantity - self.delivered_quantity

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining to invoice."""
        return self.quantity - self.invoiced_quantity

    @property
    def received_percentage(self) -> float:
        """Calculate received percentage for this line."""
        if self.quantity == 0:
            return 100.0
        return float((self.received_quantity / self.quantity) * 100)
