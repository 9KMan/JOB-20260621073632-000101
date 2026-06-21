# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes from suppliers or OCR processing with evidence of delivery.
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note header model.

    Represents a delivery note with supplier delivery information.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_supplier_number", "supplier_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_deleted_at", "deleted_at"),
    )

    # DN identification
    dn_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Reference to PO
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial totals
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.SUBMITTED,
        index=True,
    )

    # Notes
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Delivery address
    delivery_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Carrier information
    carrier_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Audit fields
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
    )
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Signatures
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    signature_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.total_amount} {self.currency_code}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note line item model.

    Represents individual line items delivered.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_sku", "sku"),
        Index("ix_delivery_note_lines_deleted_at", "deleted_at"),
    )

    # Parent reference
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    barcode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Pricing
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Condition
    condition_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description} x {self.quantity_delivered}>"


__all__ = [
    "DeliveryNote",
    "DeliveryNoteLine",
]
