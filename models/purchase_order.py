# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from datetime import date, datetime, timezone
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import Invoice, InvoiceLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", "vendor_id", name="uq_po_vendor"),
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        {"schema": None},
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # PO dates
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50), default=PurchaseOrderStatus.ACTIVE, nullable=False, index=True
    )

    # Payment terms
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Shipping
    ship_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ship_from: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Additional info
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # ERP reference
    erp_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Closing
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

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

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount}>"

    @property
    def is_closed(self) -> bool:
        """Check if PO is closed."""
        return self.status == PurchaseOrderStatus.CLOSED or self.closed_at is not None


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_product_code", "product_code"),
        {"schema": None},
    )

    # Parent reference
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line identification
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    line_type: Mapped[str] = mapped_column(String(50), default="ITEM", nullable=False)

    # Product/Service
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manufacturer_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000")
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000")
    )
    quantity_shipped: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    # Delivery info
    promised_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    is_fully_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fully_invoiced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fully_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_po_line",
        foreign_keys="InvoiceLine.matched_po_line_id",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.product_code}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.quantity_ordered - self.quantity_received

    @property
    def invoice_remaining(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.quantity_ordered - self.quantity_invoiced
