# models/delivery_note.py
"""Delivery Note and DeliveryNoteLine SQLAlchemy models."""

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
    from models.invoice import InvoiceLine
    from models.purchase_order import POLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note header model."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
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
    po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    po_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    receipt_date: Mapped[date | None] = mapped_column(
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
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="received",
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
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
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_date", "vendor_id", "dn_date"),
        Index("ix_delivery_notes_po_number", "po_number"),
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"

    dn_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
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
        nullable=True,
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    po_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    received: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["POLine | None"] = relationship(
        "POLine",
        back_populates="delivery_note_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_line",
    )

    __table_args__ = (
        Index("ix_delivery_note_lines_dn_line", "dn_id", "line_number", unique=True),
        Index("ix_delivery_note_lines_po_line", "po_line_id"),
    )
