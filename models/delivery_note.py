// models/delivery_note.py
"""Delivery note model definition."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Date,
    Numeric,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLineItem


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery note model representing supplier deliveries.
    
    Attributes:
        id: UUID primary key
        dn_number: Unique delivery note identifier
        supplier_id: External supplier identifier
        supplier_name: Supplier name
        po_id: Reference to associated purchase order
        delivery_date: Date of delivery
        received_date: Date goods were received
        total_amount: Total delivery amount
        currency: Currency code
        status: Current delivery note status
        notes: Additional notes
        erp_reference: External ERP system reference
    """
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_supplier_id", "supplier_id"),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_status", "status"),
    )
    
    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(50),
        default=DeliveryNoteStatus.SUBMITTED,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    erp_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    line_items: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Line items for delivery notes.
    
    Attributes:
        id: UUID primary key
        dn_id: Parent delivery note reference
        po_line_id: Reference to PO line item
        line_number: Line item sequence number
        description: Item description
        quantity: Delivered quantity
        uom: Unit of measure
        notes: Line item notes
    """
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
    )
    
    dn_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36),
        ForeignKey("purchase_order_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
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
