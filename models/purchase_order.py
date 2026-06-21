# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents purchase orders from the ERP system for matching against
invoices and delivery notes.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import LineStatus, PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model representing orders to suppliers.

    Attributes:
        po_number: Unique PO identifier from ERP
        supplier_id: External supplier identifier
        supplier_name: Supplier company name
        order_date: Date PO was created
        delivery_date: Expected/requested delivery date
        status: Current PO status
        subtotal: Sum of line amounts before tax
        tax_amount: Total tax amount
        total_amount: Grand total including tax
        currency: ISO currency code
        payment_terms: Payment terms description
        shipping_address: Delivery address
    """

    __tablename__ = "purchase_orders"

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    # Financial amounts
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
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="po_status"),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Metadata
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    shipping_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
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

    __table_args__ = (
        Index("ix_po_supplier_date", "supplier_id", "order_date"),
        Index("ix_po_status_date", "status", "order_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.supplier_name}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Individual line items on a purchase order.

    Attributes:
        line_number: Line item sequence number
        sku: Product/item SKU
        description: Item description
        quantity: Ordered quantity
        unit_price: Price per unit
        line_total: quantity * unit_price
        received_quantity: Quantity received via delivery notes
        invoiced_quantity: Quantity invoiced
    """

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_orders.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Line identification
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

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="po_line_status"),
        nullable=False,
        default=LineStatus.PENDING,
    )

    # Match confidence score (0-100)
    match_score: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_po_line_po_line_num", "purchase_order_id", "line_number"),
        Index("ix_po_line_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to receive/invoice."""
        return self.quantity - self.received_quantity

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.quantity - self.invoiced_quantity

    @property
    def is_fully_received(self) -> bool:
        """Check if line is fully received."""
        return self.received_quantity >= self.quantity

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.invoiced_quantity >= self.quantity
