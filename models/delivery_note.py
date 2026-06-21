# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class DeliveryNote(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Delivery Note model representing goods received."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_receipt_date", "receipt_date"),
        Index("ix_delivery_notes_vendor_dn", "vendor_number", "dn_number"),
    )

    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        default=DeliveryNoteStatus.CONFIRMED,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), default="erp")
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    warehouse_location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} from {self.vendor_name}>"


class DeliveryNoteLine(UUIDMixin, TimestampMixin, Base):
    """Delivery Note Line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "dn_id", "line_number"),
        Index("ix_delivery_note_lines_item_number", "item_number"),
    )

    dn_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    item_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
    )
    po_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note_line",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def invoiced_quantity(self) -> Decimal:
        """Calculate the total invoiced quantity."""
        return Decimal("0.00")
