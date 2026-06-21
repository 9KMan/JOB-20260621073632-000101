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

from models.base import Base, CommonMixin
from models.enums import (
    PurchaseOrderStatus,
    SourceSystem,
    get_purchase_order_status_enum,
    get_source_system_enum,
)

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, CommonMixin):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", "vendor_id", name="uq_po_vendor"),
        Index("ix_po_vendor_id", "vendor_id"),
        Index("ix_po_po_date", "po_date"),
        Index("ix_po_status", "status"),
        Index("ix_po_expected_date", "expected_delivery_date"),
        {"schema": None},
    )

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    vendor_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # PO details
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Purchase order number",
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="PO creation date",
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
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
        get_purchase_order_status_enum(),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )

    # Source tracking
    source_system: Mapped[SourceSystem] = mapped_column(
        get_source_system_enum(),
        nullable=False,
        default=SourceSystem.ERP,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Additional fields
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    shipping_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    cost_center: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict | None] = mapped_column(
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        foreign_keys="CrossRef.po_id",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.vendor_id} - {self.status.value}>"

    @property
    def remaining_value(self) -> Decimal:
        """Calculate remaining PO value not yet invoiced."""
        invoiced = sum(bl.invoiced_amount for bl in self.balance_ledger_entries)
        return self.total_amount - invoiced


class PurchaseOrderLine(Base, CommonMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_line_po_id", "purchase_order_id"),
        Index("ix_po_line_line_number", "purchase_order_id", "line_number"),
        {"schema": None},
    )

    # Parent PO
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Ordered quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Delivery tracking
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )

    # Product reference
    product_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Quantity not yet delivered."""
        return self.quantity - self.delivered_quantity

    @property
    def remaining_invoiced_quantity(self) -> Decimal:
        """Quantity not yet invoiced."""
        return self.quantity - self.invoiced_quantity

    @property
    def delivery_percentage(self) -> float:
        """Delivery completion percentage."""
        if self.quantity == 0:
            return 0.0
        return float(self.delivered_quantity / self.quantity * 100)
