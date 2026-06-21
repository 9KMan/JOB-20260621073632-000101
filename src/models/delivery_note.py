// src/models/delivery_note.py
"""Delivery Note models."""
import decimal
import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

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

from src.database import Base
from src.models.base import BaseModel


class DeliveryNoteStatus(str, Enum):
    """Delivery Note status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_TRANSIT = "in_transit"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel):
    """Delivery Note model."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    shipment_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=DeliveryNoteStatus.DRAFT.value, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_delivery_notes_supplier_status", "supplier_id", "status"),
        Index("ix_delivery_notes_po_status", "purchase_order_id", "status"),
    )


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    received_quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_delivery_note_lines_dn_line", "delivery_note_id", "line_number", unique=True),
    )
