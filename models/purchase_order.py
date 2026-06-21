# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents POs from the ERP system.
"""

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order model representing POs from ERP.

    Attributes:
        po_number: Unique PO identifier from ERP
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        po_date: PO creation date
        delivery_date: Expected delivery date
        currency: ISO currency code
        total_amount: Total PO amount
        status: Current PO status
        department: Department/cost center
        requested_by: User who requested the PO
        approved_by: User who approved the PO
        metadata: Additional JSON metadata
    """

    __tablename__ = "purchase_orders"

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
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
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
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.SUBMITTED.value,
        index=True,
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    requested_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        nullable=True,
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
        back_populates="matched_po",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_date", "vendor_id", "po_date"),
        Index("ix_purchase_orders_status_date", "status", "po_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase order line item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("1"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.00"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    is_fully_invoiced: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_fully_received: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_pol_purchase_order_line", "purchase_order_id", "line_number"),
        UniqueConstraint("purchase_order_id", "line_number", name="uq_pol_line"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining uninvoiced quantity."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def balance(self) -> Decimal:
        """Calculate line balance (total - invoiced)."""
        return self.line_total - (self.unit_price * self.quantity_invoiced)
