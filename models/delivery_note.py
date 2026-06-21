# models/delivery_note.py
# Delivery note table and SQLAlchemy model
# AP Automation Core Engine — FinaRo

"""DeliveryNote and DeliveryNoteLine SQLAlchemy ORM models."""

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
from models.enums import (
    DeliveryNoteStatus,
    DeliveryNoteStatusType,
    LineStatus,
    LineStatusType,
)

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine
    from models.invoice import InvoiceLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note model representing goods received.

    Attributes:
        id: UUID primary key.
        dn_number: Unique delivery note number.
        vendor_id: External vendor/system identifier.
        vendor_name: Vendor name for display purposes.
        po_reference: Reference to the associated PO.
        receipt_date: Date goods were received.
        status: Current delivery note status.
        notes: Additional notes.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
        deleted_at: Soft delete timestamp.
    """

    __tablename__ = "delivery_notes"

    # Basic DN info
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique delivery note number",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="External vendor/system identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name for display",
    )
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Reference to associated PO",
    )

    # Dates
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date goods were received",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        DeliveryNoteStatusType,
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
        index=True,
        doc="Current delivery note status",
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    is_ocr_processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this DN was processed via OCR",
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Shipping carrier name",
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Shipping tracking number",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Delivery note line items",
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_date", "vendor_id", "receipt_date"),
        Index("ix_delivery_notes_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.receipt_date}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery note line item model.

    Attributes:
        id: UUID primary key.
        dn_id: Parent delivery note UUID.
        line_number: Line item number.
        description: Item description.
        quantity: Delivered quantity.
        uom: Unit of measure.
        po_line_id: Reference to matched PO line (optional).
        status: Line status.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "delivery_note_lines"

    # Foreign key
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent delivery note UUID",
    )

    # Line info
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    uom: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure",
    )

    # Matching references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched PO line",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        LineStatusType,
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line status",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
        doc="Parent delivery note",
    )

    __table_args__ = (
        Index("ix_delivery_note_lines_dn_line", "dn_id", "line_number"),
        Index("ix_delivery_note_lines_po_line", "po_line_id"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.description[:30]}>"
