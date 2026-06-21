# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Numeric,
    String,
    Text,
    Integer,
    Date,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Top-level delivery note (DN / Goods Receipt Note) header.

    Attributes
    ----------
    dn_number : str
        Unique business key for the delivery note.
    vendor_id : str
        External vendor identifier.
    vendor_name : str
        Human-readable vendor name.
    issue_date : date
        Date the goods were dispatched / received.
    po_reference : str | None
        Optional ERP PO reference string (not a FK — may be free-text).
    status : DeliveryNoteStatus
        Current lifecycle status.
    notes : str | None
        Free-text notes.
    """

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[uuid.date] = mapped_column(nullable=False)
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(30),
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_status_deleted", "status", "is_deleted"),
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """
    Individual line item on a delivery note.

    Attributes
    ----------
    line_number : int
        1-based position within the DN.
    description : str
        Line item description.
    sku : str | None
        Product / SKU identifier.
    quantity : Decimal
        Delivered quantity.
    unit_of_measure : str
        UoM string.
    po_line_id : uuid.UUID | None
        Foreign key to the linked PurchaseOrderLine (set by cascade matching).
    status : LineStatus
        Current matching status.
    """

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="PCS")
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LineStatus.OPEN,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────

    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_line",
        foreign_keys=[po_line_id],
    )

    __table_args__ = (
        UniqueConstraint("delivery_note_id", "line_number", name="uq_dn_line_number"),
        Index("ix_dn_lines_sku", "sku"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
    )
