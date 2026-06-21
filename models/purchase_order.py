# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
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

from models.base import Base, CompanyMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import CurrencyCode, PurchaseOrderStatus, LineType

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyMixin):
    """Purchase Order database model.

    Represents a PO issued to a supplier, which serves as the primary
    anchor for invoice matching.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", "company_code", name="uq_po_number_company"),
        Index("ix_purchase_orders_supplier_code", "supplier_code"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_expected_date", "expected_delivery_date"),
        {"schema": None},
    )

    # Reference fields
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    external_po_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Supplier information
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    supplier_contact: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    supplier_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Date fields
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    confirmed_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial fields
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
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
    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    other_charges: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT.value,
        index=True,
    )

    # Terms
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    delivery_terms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Flags
    is_blanket_po: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_rush: Mapped[bool] = mapped_column(
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
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        lazy="selectin",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"

    @property
    def is_open(self) -> bool:
        """Check if PO is still open for matching."""
        return self.status in [
            PurchaseOrderStatus.SENT.value,
            PurchaseOrderStatus.CONFIRMED.value,
            PurchaseOrderStatus.PARTIAL.value,
        ]

    @property
    def is_overdue(self) -> bool:
        """Check if PO is past expected delivery date."""
        if self.expected_delivery_date is None:
            return False
        return date.today() > self.expected_delivery_date and not self.is_complete

    @property
    def is_complete(self) -> bool:
        """Check if PO is fully delivered and invoiced."""
        return self.status in [
            PurchaseOrderStatus.COMPLETE.value,
            PurchaseOrderStatus.CLOSED.value,
        ]


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase Order Line Item database model.

    Represents individual line items on a PO for line-level matching
    against invoice lines and delivery note lines.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_sku", "sku"),
        {"schema": None},
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    external_line_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Product/Service identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    line_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=LineType.STANDARD.value,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_cancelled: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Tax
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Delivery
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.quantity_ordered - self.quantity_delivered - self.quantity_cancelled

    @property
    def quantity_pending_invoice(self) -> Decimal:
        """Calculate quantity pending to be invoiced."""
        return self.quantity_delivered - self.quantity_invoiced

    @property
    def is_fully_delivered(self) -> bool:
        """Check if line is fully delivered."""
        return self.quantity_delivered >= self.quantity_ordered

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.quantity_invoiced >= self.quantity_delivered

    @property
    def delivery_percentage(self) -> float:
        """Calculate delivery percentage."""
        if self.quantity_ordered == 0:
            return 100.0
        return float(self.quantity_delivered / self.quantity_ordered * 100)
