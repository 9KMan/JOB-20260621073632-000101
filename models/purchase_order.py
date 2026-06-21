// models/purchase_order.py
"""
PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Purchase orders represent confirmed buying commitments to vendors.
They serve as the anchoring reference for invoice matching.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import (
    PurchaseOrderStatus,
    LineStatus,
    po_status_enum,
    line_status_enum,
)

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.delivery_note import DeliveryNote, DeliveryNoteLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """
    Purchase Order header table.
    
    Represents a confirmed purchase order sent to a vendor.
    Serves as the primary reference for invoice matching.
    """

    __tablename__ = "purchaseorders"

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Purchase order number",
    )
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Vendor identifier code",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor display name",
    )

    # Date fields
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Purchase order date",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="PO expiration date",
    )

    # Financial details
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
        doc="Total PO amount including tax",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        po_status_enum,
        nullable=False,
        default=PurchaseOrderStatus.ACTIVE,
        index=True,
        doc="Current PO status",
    )

    # Reference fields
    buyer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Buyer contact name",
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Requesting department",
    )
    cost_center: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Cost center code",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="External system reference (ERP, etc.)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="PO description or notes",
    )

    # JSON metadata
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
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
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_po_vendor_date", "vendor_code", "po_date"),
        Index("ix_po_status_date", "status", "po_date"),
        Index("ix_po_external_ref", "external_reference"),
    )

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrder(id={self.id}, "
            f"po_number={self.po_number}, "
            f"vendor={self.vendor_code}, "
            f"amount={self.total_amount})>"
        )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """
    Purchase Order Line item table.
    
    Represents individual line items on a purchase order.
    Used for detailed matching against invoices and delivery notes.
    """

    __tablename__ = "purchaseorder_lines"

    # Foreign key
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )

    # Product/Service identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU or part number",
    )
    gtin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Global Trade Item Number",
    )
    manufacturer_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Manufacturer's part number",
    )

    # Quantities
    ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Originally ordered quantity",
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Total quantity received across all DNs",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Total quantity invoiced",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure code",
    )

    # Financial details
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Agreed unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total (quantity * unit_price)",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        line_status_enum,
        nullable=False,
        default=LineStatus.OPEN,
        doc="Line matching status",
    )

    # Delivery tracking
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        compute_only=True,
        doc="Remaining quantity to receive",
    )

    # Metadata
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Tax classification code",
    )
    delivery_schedule: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Delivery schedule information",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_pol_line",
        foreign_keys="InvoiceLine.matched_pol_line_id",
    )
    matched_delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_po_line",
        foreign_keys="DeliveryNoteLine.matched_po_line_id",
    )

    __table_args__ = (
        Index("ix_pol_po_line", "purchase_order_id", "line_number"),
        Index("ix_pol_sku", "sku"),
    )

    def calculate_remaining(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.ordered_quantity - self.received_quantity

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrderLine(id={self.id}, "
            f"po={self.purchase_order_id}, "
            f"line={self.line_number}, "
            f"sku={self.sku}, "
            f"qty={self.ordered_quantity})>"
        )
