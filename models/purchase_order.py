# models/purchase_order.py
"""Purchase order and purchase order line models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.delivery_note import DeliveryNoteLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order header model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
    )

    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    po_date: Mapped[date] = mapped_column(
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
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        default="erp",
        nullable=False,
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    cost_center: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase order line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "po_id", "line_number"),
    )

    po_id: Mapped[str] = mapped_column(
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
    ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    item_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.description}>"

    @property
    def balance_quantity(self) -> Decimal:
        """Calculate remaining balance to receive."""
        return self.ordered_quantity - self.received_quantity

    @property
    def invoice_balance(self) -> Decimal:
        """Calculate remaining balance to invoice."""
        return self.received_quantity - self.invoiced_quantity
