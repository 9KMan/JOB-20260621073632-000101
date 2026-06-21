// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents purchase orders from the ERP system for anchoring.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase order model from ERP system.

    Serves as the anchor document for invoice matching.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_created_at", "created_at"),
        UniqueConstraint("vendor_id", "po_number", name="uq_vendor_po"),
    )

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor display name",
    )
    vendor_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Vendor address",
    )

    # PO Details
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Purchase order number",
    )
    po_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="PO date (YYYY-MM-DD)",
    )
    required_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Required delivery date (YYYY-MM-DD)",
    )

    # Financial Information
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )
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
        doc="Total tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="PO total amount",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.APPROVED.value,
        index=True,
        doc="Current PO status",
    )

    # Additional Fields
    buyer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Buyer/requisitioner name",
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Department code",
    )
    project_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Project/cost center code",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment terms",
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
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} from {self.vendor_id}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Individual line item on a purchase order.

    Each line represents a product or service to be purchased.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "purchase_order_id"),
        Index("ix_po_lines_line_number", "purchase_order_id", "line_number"),
        Index("ix_po_lines_sku", "sku"),
    )

    # Foreign Key
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent purchase order ID",
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )

    # Product Information
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU/UPC",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Internal product code",
    )
    manufacturer_part: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Manufacturer part number",
    )

    # Quantity and Pricing
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Received quantity",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Line-level tax amount",
    )

    # Delivery Tracking
    required_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Required delivery date (YYYY-MM-DD)",
    )
    promised_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Promised delivery date (YYYY-MM-DD)",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.sku or 'No SKU'}>"
