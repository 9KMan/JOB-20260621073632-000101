# models/purchase_order.py
"""Purchase Order model for AP Automation Engine."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model representing PO documents from ERP.

    Attributes:
        po_number: Unique PO number
        vendor_id: External vendor identifier
        vendor_name: Name of the vendor
        po_date: Date of the PO
        delivery_date: Expected delivery date
        subtotal: PO subtotal before tax
        tax_amount: Tax amount
        total_amount: Total PO amount
        currency: Currency code (ISO 4217)
        status: Current PO status
        notes: Additional notes
        metadata: JSON metadata for extensibility
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_created_at", "created_at"),
    )

    # Basic Information
    po_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        doc="Unique PO number",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="External vendor identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the vendor",
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date of the PO",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )

    # Financial Information
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="PO subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total PO amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="approved",
        doc="Current PO status",
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether PO is closed",
    )

    # Additional Information
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="JSON metadata for extensibility",
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
        doc="Source system (erp, manual)",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    balance_ledgers: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        foreign_keys="BalanceLedger.po_id",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        foreign_keys="CrossRef.po_id",
    )


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase Order Line item model.

    Attributes:
        po_id: Parent purchase order ID
        line_number: Line item number
        description: Item description
        quantity: Ordered quantity
        unit_price: Price per unit
        amount: Total line amount
        delivered_qty: Quantity already delivered
        invoiced_qty: Quantity already invoiced
        open_qty: Remaining quantity (quantity - delivered_qty)
        tax_code: Tax code
        accounting_code: Cost center / GL account
        expected_delivery_date: Expected delivery date for this line
        status: Line status
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_accounting_code", "accounting_code"),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent purchase order ID",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )

    # Quantities
    delivered_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity already delivered",
    )
    invoiced_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity already invoiced",
    )
    accepted_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity accepted",
    )

    # Tax and Accounting
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Tax code",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Line tax amount",
    )
    accounting_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Cost center / GL account",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
        doc="Line status",
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date for this line",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys="DeliveryNoteLine.po_line_id",
    )

    @property
    def open_qty(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.quantity - self.delivered_qty

    @property
    def open_amount(self) -> Decimal:
        """Calculate remaining amount to be invoiced."""
        return Decimal(str(self.open_qty)) * self.unit_price


# Add JSONB import at runtime
from sqlalchemy.dialects.postgresql import JSONB

PurchaseOrder.__table__.c.metadata = Base.metadata
PurchaseOrderLine.__table__.c.metadata = Base.metadata
