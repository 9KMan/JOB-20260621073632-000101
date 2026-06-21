// models/purchase_order.py
"""PurchaseOrder and POLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryMixin
from models.enums import POStatus

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.delivery_note import DeliveryNoteLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDPrimaryMixin, TimestampMixin, SoftDeleteMixin):
    """
    Purchase Order header record sourced from the ERP system.

    The PO is the financial contract against which invoices are matched.
    The anchoring layer identifies the correct PO for each invoice.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
    )

    po_number: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    po_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[POStatus] = mapped_column(
        String(30), nullable=False, default=POStatus.ACTIVE, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="ERP system PO ID"
    )
    is_anchored: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="Whether a valid invoice has been anchored to this PO"
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="po_reference",
        lazy="selectin",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class POLine(Base, UUIDPrimaryMixin, TimestampMixin):
    """
    Individual line item on a Purchase Order.

    The cascade layer matches invoice lines to PO lines based on
    SKU, description similarity, and quantity tolerance.
    """

    __tablename__ = "po_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_sku", "sku"),
        Index("ix_po_lines_po_id_line_number", "po_id", "line_number", unique=True),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000")
    )
    delivered_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    invoiced_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        lazy="selectin",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="po_line_dn_lines",
        back_populates="po_lines",
        lazy="selectin",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ── Junction Table: POLine ↔ DeliveryNoteLine ─────────────────────────────────

from sqlalchemy import Table, Column, ForeignKey
from models.base import Base as _Base2

po_line_dn_lines = Table(
    "po_line_dn_lines",
    _Base2.metadata,
    Column(
        "po_line_id",
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "delivery_note_line_id",
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
