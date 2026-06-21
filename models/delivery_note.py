# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import Invoice


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model representing goods received."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_receipt_date", "receipt_date"),
        Index("ix_delivery_notes_status", "status"),
        {
            "schema": None,
        },
    )

    # Vendor Information
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # DN Details
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Reference
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(30),
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
    )

    # Additional Info
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ERP Reference
    erp_dn_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_note",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, number={self.dn_number}, status={self.status})>"


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery Note line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_line_number", "line_number"),
        Index("ix_dn_lines_sku", "sku"),
        {
            "schema": None,
        },
    )

    # Parent Reference
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Product/Service
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), nullable=False, default=Decimal("0")
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")

    # Matching
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line={self.line_number}, sku={self.sku})>"
