# models/purchase_order.py
"""
Purchase Order and POLine SQLAlchemy models.

POs are the primary anchor for invoice matching.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin
from models.enums import POStatus

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.delivery_note import DeliveryNote
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base, SoftDeleteMixin):
    """
    Purchase Order header record.
    
    POs are ingested from ERP and serve as the anchor
    for invoice matching.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", "supplier_id", name="uq_po_number_supplier"),
        UniqueConstraint("external_po_id", name="uq_external_po_id"),
        Index("ix_pos_status", "status"),
        Index("ix_pos_supplier_id", "supplier_id"),
        Index("ix_pos_po_date", "po_date"),
        Index("ix_pos_created_at", "created_at"),
        {
            "comment": "Purchase Order header table for AP automation",
        },
    )

    # ─── External Identifiers ─────────────────────────────────────────────────
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Internal PO number",
    )
    external_po_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="ERP/external PO reference ID",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Supplier/vendor identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Supplier name",
    )
    supplier_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Supplier tax identification number",
    )

    # ─── Financial ───────────────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
        comment="ISO 4217 currency code",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="PO total amount in PO currency",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Tax amount",
    )

    # ─── Dates ───────────────────────────────────────────────────────────────
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="PO issue date",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Expected/required delivery date",
    )

    # ─── Status ──────────────────────────────────────────────────────────────
    status: Mapped[POStatus] = mapped_column(
        POStatus.db_type(),
        nullable=False,
        default=POStatus.DRAFT,
        index=True,
        comment="PO status",
    )

    # ─── Notes ───────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes",
    )
    terms: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Payment terms",
    )

    # ─── Relations ───────────────────────────────────────────────────────────
    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        foreign_keys="CrossRef.po_id",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        secondary="po_delivery_notes",
        back_populates="purchase_orders",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} ({self.status.value})>"

    @property
    def total_lines_count(self) -> int:
        """Return total number of line items."""
        return len(self.lines)

    @property
    def is_active(self) -> bool:
        """Check if PO is in an active state."""
        return self.status in POStatus.active_statuses()

    @property
    def is_open(self) -> bool:
        """Check if PO is open for invoice matching."""
        return self.status in POStatus.open_statuses()

    def get_remaining_balance(self) -> Decimal:
        """Calculate remaining invoiceable amount."""
        from sqlalchemy import select, func as sql_func
        # This would be calculated from balance_ledger
        return self.total_amount

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a summary dictionary for listings."""
        return {
            "id": str(self.id),
            "po_number": self.po_number,
            "external_po_id": self.external_po_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "po_date": self.po_date.isoformat() if self.po_date else None,
            "total_amount": str(self.total_amount),
            "currency": self.currency,
            "status": self.status.value,
        }


class POLine(Base):
    """
    Individual line item on a Purchase Order.
    
    Each line represents a product/service being ordered and will
    be matched against corresponding Invoice lines.
    """

    __tablename__ = "po_lines"
    __table_args__ = (
        UniqueConstraint("po_id", "line_number", name="uq_po_line_number"),
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_product_code", "product_code"),
        {
            "comment": "Purchase Order line items for AP automation",
        },
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Line Identification ─────────────────────────────────────────────────
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line item sequence number on PO",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Line item description",
    )

    # ─── Product ──────────────────────────────────────────────────────────────
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product/SKU code",
    )
    product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Product name",
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure",
    )

    # ─── Quantities & Prices ──────────────────────────────────────────────────
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Ordered quantity",
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Received quantity (from delivery notes)",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Invoiced quantity",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Line total (quantity_ordered * unit_price)",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Tax rate",
    )

    # ─── Relations ───────────────────────────────────────────────────────────
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        foreign_keys="InvoiceLine.po_line_id",
        back_populates="po_line",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<POLine {self.line_number}: {self.description[:30]}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining invoiceable quantity."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def line_amount_remaining(self) -> Decimal:
        """Calculate remaining invoiceable amount."""
        return self.quantity_remaining * self.unit_price

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a summary dictionary."""
        return {
            "id": str(self.id),
            "po_id": str(self.po_id),
            "line_number": self.line_number,
            "description": self.description,
            "product_code": self.product_code,
            "quantity_ordered": str(self.quantity_ordered),
            "quantity_received": str(self.quantity_received),
            "quantity_invoiced": str(self.quantity_invoiced),
            "quantity_remaining": str(self.quantity_remaining),
            "unit_price": str(self.unit_price),
            "line_amount": str(self.line_amount),
            "uom": self.uom,
        }


# Association table for PO <-> DeliveryNote (many-to-many)
from sqlalchemy import Table, Column

po_delivery_notes = Table(
    "po_delivery_notes",
    Base.metadata,
    Column("po_id", UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), primary_key=True),
    Column("delivery_note_id", UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), primary_key=True),
)
