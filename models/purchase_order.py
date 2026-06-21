# models/purchase_order.py
"""Purchase Order model for AP Automation Core Engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
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
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrderLine(TimestampMixin, UUIDPrimaryKeyMixin, Base):
    """Individual line item on a Purchase Order."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_line_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Product/Service info
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
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
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Delivery info
    promised_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Tax info
    tax_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hsn_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_po_line",
        foreign_keys="InvoiceLine.matched_po_line_id",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="po_line",
    )

    __table_args__ = (
        Index("ix_po_lines_po_sku", "purchase_order_id", "sku"),
    )

    @property
    def balance_quantity(self) -> Decimal:
        """Calculate remaining uninvoiced quantity."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def balance_amount(self) -> Decimal:
        """Calculate remaining uninvoiced amount."""
        return self.line_total - (self.unit_price * self.quantity_invoiced)


class PurchaseOrder(TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin, Base):
    """Purchase Order model representing POs from ERP systems.

    POs are the anchor for invoice matching. Invoices must be matched
    against POs based on line items, pricing, and quantities.
    """

    __tablename__ = "purchase_orders"

    # External reference
    external_po_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Supplier info
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # PO dates
    po_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial info
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(15, 6),
        nullable=False,
        default=Decimal("1"),
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Discount info
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )
    is_blanket_po: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Source info
    source_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Payment info
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Approval info
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number",
    )
    matched_invoices: Mapped[list["PurchaseOrder"]] = relationship(
        "Invoice",
        foreign_keys="Invoice.matched_po_id",
        back_populates="matched_po",
    )

    __table_args__ = (
        Index("ix_pos_supplier_date", "supplier_id", "po_date"),
        Index("ix_pos_status_date", "status", "po_date"),
        Index("ix_pos_supplier_po", "supplier_id", "po_number"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"

    @property
    def total_ordered_quantity(self) -> Decimal:
        """Total quantity across all lines."""
        return sum(line.quantity_ordered for line in self.lines)

    @property
    def total_received_quantity(self) -> Decimal:
        """Total received quantity across all lines."""
        return sum(line.quantity_received for line in self.lines)

    @property
    def total_invoiced_quantity(self) -> Decimal:
        """Total invoiced quantity across all lines."""
        return sum(line.quantity_invoiced for line in self.lines)


__all__ = ["PurchaseOrder", "PurchaseOrderLine"]
