# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatusType


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery Note / Goods Receipt Note header record."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_vendor_code", "vendor_code"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_po_id", "po_id"),
    )

    dn_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Linked PO
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Dates
    dn_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    status: Mapped[DeliveryNoteStatusType] = mapped_column(
        DeliveryNoteStatusType,
        default=DeliveryNoteStatusType.RECEIVED,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Relationships ─────────────────────────────────────────────────────────

    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} status={self.status}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Line item on a Delivery Note."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Matched PO Line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_line: Mapped["POLine | None"] = relationship(
        "POLine",
        foreign_keys=[po_line_id],
    )

    # Matched Invoice Line
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} qty={self.quantity_delivered}>"
