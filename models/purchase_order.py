# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedgerEntry
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order document model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_erp_po_id", "erp_po_id"),
        UniqueConstraint("po_number", name="uq_purchase_orders_po_number"),
    )

    # Document reference fields
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Purchase order number",
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Vendor name",
    )

    # PO dates
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="PO creation date",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Expected delivery date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PO subtotal",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total PO amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        default=DocumentStatus.PENDING,
        nullable=False,
        comment="PO status",
    )

    # ERP reference
    erp_po_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="External ERP PO ID",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, status={self.status})>"


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_line_number", "line_number"),
        Index("ix_po_lines_sku", "sku"),
        Index("ix_po_lines_status", "status"),
        UniqueConstraint("po_id", "line_number", name="uq_po_lines_po_id_line_number"),
    )

    # Foreign key to purchase order
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line reference
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line item sequence number",
    )

    # Product/service info
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product SKU",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Ordered quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Unit price",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Line total amount",
    )

    # Delivered quantity tracking
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Total delivered quantity",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Total invoiced quantity",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        default=LineStatus.OPEN,
        nullable=False,
        comment="Line status",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
    )
    matched_delivery_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    balance_entries: Mapped[list["BalanceLedgerEntry"]] = relationship(
        "BalanceLedgerEntry",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity - self.quantity_invoiced

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.quantity_invoiced >= self.quantity

    @property
    def is_fully_delivered(self) -> bool:
        """Check if line is fully delivered."""
        return self.quantity_delivered >= self.quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line_number={self.line_number}, qty={self.quantity})>"
