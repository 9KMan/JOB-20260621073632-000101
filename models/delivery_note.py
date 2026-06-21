# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes from suppliers/ERP.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note model representing deliveries from vendors.

    Attributes:
        dn_number: Unique delivery note identifier
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        po_reference: Reference to related PO
        dn_date: Date of delivery
        received_date: Date goods were received
        currency: ISO currency code
        total_amount: Total delivery amount
        status: Current DN status
        received_by: User who received the goods
        notes: Additional notes
    """

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DeliveryNoteStatus.ISSUED.value,
        index=True,
    )
    received_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
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
        UniqueConstraint("dn_number", "vendor_id", name="uq_dn_vendor"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.total_amount} {self.currency}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("1"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.00"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    matched_pol_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_inv_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_dnl_delivery_note_line", "delivery_note_id", "line_number"),
        UniqueConstraint("delivery_note_id", "line_number", name="uq_dn_line"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"
