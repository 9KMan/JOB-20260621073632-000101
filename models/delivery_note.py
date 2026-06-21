// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Delivery notes (or Goods Receipt Notes) record physical deliveries
and are used to verify invoice quantities.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import DeliveryNoteStatus


class DeliveryNote(Base):
    """Delivery note header model.

    Represents a delivery note or goods receipt note.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_vendor_code", "vendor_code"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_receipt_date", "receipt_date"),
    )

    # External references
    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Reference to PO
    po_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    po_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Dates
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        DeliveryNoteStatus,
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
    )

    # Source tracking
    source: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False,
    )  # manual, erp, ocr

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    matched_invoices: Mapped[list[str]] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default=[],
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} ({self.status.value})>"


class DeliveryNoteLine(Base):
    """Delivery note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_sku", "sku"),
    )

    # Parent reference
    dn_id: Mapped[UUID] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Quantities
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    # Matching references
    matched_po_line_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_invoice_line_ids: Mapped[list[UUID] | None] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default=[],
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        foreign_keys=[matched_po_line_id],
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
