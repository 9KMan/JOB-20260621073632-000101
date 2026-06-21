// models/delivery_note.py
"""Delivery Note model and related data structures."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.invoice import InvoiceLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model representing a goods receipt note."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_number", "po_number"),
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_received_date", "received_date"),
    )

    # DN Header
    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Dates
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Reference to PO
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Financials
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    
    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(30),
        default=DeliveryNoteStatus.ISSUED,
        nullable=False,
    )
    
    # Additional info
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
        Index("ix_dn_lines_status", "status"),
    )

    # Foreign keys
    dn_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Line information
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Product info
    item_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    item_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Quantities
    delivered_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    accepted_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    rejected_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"))
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
    )
    
    # Unit price from PO
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
    )
