# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model representing orders to suppliers."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_status", "status"),
        {
            "schema": None,
        },
    )

    # Vendor Information
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PO Details
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(30),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
    )

    # Additional Info
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ERP Reference
    erp_po_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="po",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, number={self.po_number}, status={self.status})>"


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase Order line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_line_number", "line_number"),
        Index("ix_po_lines_sku", "sku"),
        Index("ix_po_lines_product_code", "product_code"),
        {
            "schema": None,
        },
    )

    # Parent Reference
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Product/Service
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities & Prices
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), nullable=False, default=Decimal("0")
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), nullable=False, default=Decimal("0")
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Dates
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    balance_ledger: Mapped["BalanceLedger | None"] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        uselist=False,
        lazy="selectin",
    )

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def amount_remaining(self) -> Decimal:
        """Calculate remaining amount to invoice."""
        return self.unit_price * self.quantity_remaining

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line={self.line_number}, sku={self.sku})>"
