# models/delivery_note.py
"""Delivery note and delivery note line models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note header model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
    )

    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="confirmed",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        default="erp",
        nullable=False,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
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

    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.dn_date}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery note line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
    )

    dn_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    po_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    is_invoiced: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.description}>"
