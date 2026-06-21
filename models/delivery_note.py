// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes from suppliers or OCR processing.
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note header model.

    Represents a delivery note from the supplier or OCR processing.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_vendor_code", "vendor_code"),
        Index("ix_delivery_notes_po_number", "po_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        {"schema": None},
    )

    # DN Identification
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Dates
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=True)
    shipment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        DocumentStatus.db_type(),
        nullable=False,
        default=DocumentStatus.RECEIVED,
        index=True,
    )

    # Source
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    is_ocr_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Additional Info
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "delivery_note_id"),
        Index("ix_dn_lines_po_line_id", "purchase_order_line_id"),
        Index("ix_dn_lines_item_code", "item_code"),
        {"schema": None},
    )

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/SKU
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    quantity_accepted: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    quantity_rejected: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Pricing
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    line_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # PO Line Reference
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Delivery
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Matching
    match_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"
