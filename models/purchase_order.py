# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

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
from models.enums import LineStatus, PurchaseOrderStatus

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNoteLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"

    # Supplier Information
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Supplier/Vendor ID",
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Supplier/Vendor name",
    )
    supplier_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Supplier address",
    )

    # PO Details
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        doc="Purchase Order number",
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="PO creation date",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code (ISO 4217)",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Total PO amount",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
        doc="PO status",
    )

    # Additional Information
    buyer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Buyer name",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    is_blanket_po: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is a blanket PO",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_supplier", "supplier_id"),
        Index("ix_purchase_orders_status_date", "status", "po_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.supplier_name}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"

    # Parent Reference
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent PO ID",
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Product/Item code",
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Product category",
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=False,
        doc="Received quantity",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
        doc="Unit of measure",
    )

    # Pricing
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
    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Tax code",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Tax rate percentage",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
        doc="Line status",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="purchase_order_line",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_purchase_order_lines_po_number", "purchase_order_id", "line_number"),
        Index("ix_purchase_order_lines_product", "product_code"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.quantity_ordered - self.quantity_received

    @property
    def quantity_to_invoice(self) -> Decimal:
        """Calculate quantity available to invoice."""
        return self.quantity_received - self.quantity_invoiced
