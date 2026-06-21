# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import PurchaseOrderStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import Invoice, InvoiceLine


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header model.

    Represents a purchase order issued to a vendor.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_pos_po_number", "po_number", unique=True),
        Index("ix_pos_vendor_number", "vendor_number"),
        Index("ix_pos_status", "status"),
        Index("ix_pos_issue_date", "issue_date"),
        Index("ix_pos_expected_date", "expected_date"),
        Index("ix_pos_created_at", "created_at"),
        {"schema": None},
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Dates
    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financials
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
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(30),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )

    # Delivery tracking
    total_lines: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Metadata
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    raw_data: Mapped[dict | None] = mapped_column(
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
        back_populates="purchase_order",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.vendor_number}>"

    @property
    def is_expired(self) -> bool:
        """Check if PO has expired."""
        if self.expiration_date is None:
            return False
        return date.today() > self.expiration_date

    @property
    def is_closed(self) -> bool:
        """Check if PO is closed."""
        return self.status == PurchaseOrderStatus.CLOSED

    @property
    def receipt_percentage(self) -> float:
        """Calculate receipt percentage."""
        if self.total_quantity == 0:
            return 0.0
        return float(self.received_quantity / self.total_quantity)

    @property
    def invoice_percentage(self) -> float:
        """Calculate invoiced percentage."""
        if self.total_amount == 0:
            return 0.0
        invoiced = sum(inv.total_amount for inv in self.invoices)
        return float(invoiced / self.total_amount)


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase Order line item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_line_number", "line_number"),
        Index("ix_po_lines_product_number", "product_number"),
        Index("ix_po_lines_status", "status"),
        {"schema": None},
    )

    # Parent reference
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product identification
    product_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
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

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
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
        default=Decimal("0"),
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LineStatus.OPEN,
        index=True,
    )

    # Delivery Note Line references
    delivery_note_line_ids: Mapped[list[uuid.UUID]] = mapped_column(
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        lazy="selectin",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        lazy="selectin",
    )
    balance_ledger: Mapped["BalanceLedger | None"] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def balance_quantity(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def balance_amount(self) -> Decimal:
        """Calculate remaining amount to be invoiced."""
        return self.line_amount - (self.quantity_invoiced * self.unit_price)

    @property
    def is_fully_received(self) -> bool:
        """Check if line is fully received."""
        return self.quantity_received >= self.quantity_ordered

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.quantity_invoiced >= self.quantity_ordered
