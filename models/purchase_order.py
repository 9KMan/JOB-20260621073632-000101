// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
    )

    # Vendor Information
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PO Details
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    po_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.SUBMITTED.value,
        nullable=False,
    )

    # ERP Reference
    erp_po_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), default="erp", nullable=False)

    # Approval
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.vendor_name}>"


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_sku", "sku"),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Product Information
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Quantities and Pricing
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Delivery tracking
    expected_delivery_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

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
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    @property
    def quantity_open(self) -> Decimal:
        """Calculate open quantity (ordered - received)."""
        return self.quantity_ordered - self.quantity_received

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"


from models.balance_ledger import BalanceLedger  # noqa: E402, F401
from models.invoice import InvoiceLine  # noqa: E402, F401
