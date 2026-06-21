# models/delivery_note.py
"""Delivery Note model for AP Automation Core Engine."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLineItem


class DeliveryNoteLineItem(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Line items for a delivery note."""

    __tablename__ = "delivery_note_line_items"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=True)
    po_line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_line_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="line_items",
    )
    po_line_item: Mapped["PurchaseOrderLineItem | None"] = relationship(
        "PurchaseOrderLineItem",
        back_populates="delivery_note_lines",
    )

    __table_args__ = (
        Index("ix_delivery_note_line_items_dn_id", "delivery_note_id"),
        Index("ix_delivery_note_line_items_po_line_id", "po_line_item_id"),
    )


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Delivery Note model representing deliveries from suppliers.
    
    Attributes:
        id: UUID primary key
        dn_number: Unique delivery note number
        supplier_id: External supplier identifier
        supplier_name: Supplier name
        po_reference: Reference to related PO
        delivery_date: Date of delivery
        status: Current delivery note status
        notes: Additional notes
        metadata: Additional JSON metadata
    """

    __tablename__ = "delivery_notes"

    # Core fields
    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dates
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        default=DeliveryNoteStatus.CONFIRMED,
        nullable=False,
    )

    # Additional info
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(nullable=True)

    # Relationships
    line_items: Mapped[list["DeliveryNoteLineItem"]] = relationship(
        "DeliveryNoteLineItem",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_supplier_id", "supplier_id"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_is_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} from {self.supplier_name}>"
