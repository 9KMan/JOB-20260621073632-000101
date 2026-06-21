# models/purchase_order.py
"""Purchase Order and POLine SQLAlchemy models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.invoice import InvoiceLine
    from models.delivery_note import DeliveryNoteLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header model."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(50),
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
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        index=True,
    )
    po_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="standard",
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    ship_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_blanket: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    blanket_po_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    external_ref: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    blanket_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        remote_side="PurchaseOrder.id",
        back_populates="release_orders",
    )
    release_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="blanket_po",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_date", "vendor_id", "po_date"),
        Index("ix_purchase_orders_status_created", "status", "created_at"),
    )


class POLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "po_lines"

    po_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    schedule_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    promised_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_po_lines_po_line", "po_id", "line_number", unique=True),
        Index("ix_po_lines_part_number", "part_number"),
    )
