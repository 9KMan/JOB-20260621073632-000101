# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes/receipts from warehouse or logistics.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.cross_ref import CrossRef


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery note model representing goods received.

    Attributes:
        dn_number: Unique delivery note number
        vendor_id: Vendor identifier
        vendor_name: Vendor name
        receipt_date: Date goods were received
        po_reference: Reference to related purchase order
        status: DN status
    """

    __tablename__ = "delivery_notes"

    # DN identification
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(500), nullable=False)

    # References
    po_reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    gr_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dates
    shipment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        DeliveryNoteStatus.as_enum(),
        nullable=False,
        default=DeliveryNoteStatus.RECEIVED,
        index=True,
    )

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Additional
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_dn_vendor_date", "vendor_id", "receipt_date"),
        Index("ix_dn_po_ref", "po_reference"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.receipt_date}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"

    # Parent reference
    delivery_note_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line item details
    line_number: Mapped[int] = mapped_column(nullable=False, default=1)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Quantity and pricing
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Matching references
    po_line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Match status
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Quality
    quality_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_dn_line_sku", "sku"),
        Index("ix_dn_line_po_ref", "po_line_reference"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description} x{self.quantity_delivered}>"
