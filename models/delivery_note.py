// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import POLine


class DeliveryNote(Base, UUIDPrimaryMixin, TimestampMixin, SoftDeleteMixin):
    """
    Delivery Note (DN) / Goods Receipt Note header.

    Sourced from the ERP system or OCR processing of supplier delivery paperwork.
    Used as a proof-of-delivery reference in the cascade layer.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
    )

    dn_number: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    po_reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(30), nullable=False, default=DeliveryNoteStatus.CONFIRMED, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="ERP system DN ID"
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DeliveryNoteLine(Base, UUIDPrimaryMixin, TimestampMixin):
    """
    Individual line item on a Delivery Note.

    Referenced by the cascade layer to confirm that goods were
    received before an invoice line is approved.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_sku", "sku"),
        Index("ix_dn_lines_dn_id_line_number", "dn_id", "line_number", unique=True),
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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

    # ── Relationships ──────────────────────────────────────────────────────────
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    po_lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        secondary="po_line_dn_lines",
        back_populates="delivery_note_lines",
        lazy="selectin",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        secondary="invoice_line_dn_lines",
        back_populates="delivery_note_lines",
        lazy="selectin",
    )
