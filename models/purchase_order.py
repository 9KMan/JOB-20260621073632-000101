// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine database models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, TimestampMixin):
    """Purchase order header model.

    Represents a purchase order created in the ERP system.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_created_date", "created_date"),
        UniqueConstraint("po_number", name="uq_po_number"),
        {"schema": "public"},
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    external_po_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Vendor information
    vendor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Dates
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    required_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promised_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Currency
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.APPROVED,
        index=True,
    )

    # Approval
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Additional data
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Lines relationship
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(Base, TimestampMixin):
    """Purchase order line item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        {"schema": "public"},
    )

    # Foreign key
    po_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public.purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Product reference
    product_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Delivery info
    required_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promised_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Unit of measure
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
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
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.quantity - self.received_quantity

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity - self.invoiced_quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"
