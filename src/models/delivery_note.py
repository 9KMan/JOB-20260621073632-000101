// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.match import Match


class DeliveryNoteStatus(str, Enum):
    """Delivery Note status enumeration."""

    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETE = "complete"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel):
    """Delivery Note model - one of the three documents in 3-way matching."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reference_po_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        index=True,
        nullable=True,
    )
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        SQLEnum(DeliveryNoteStatus, name="delivery_note_status"),
        default=DeliveryNoteStatus.RECEIVED,
        nullable=False,
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    received_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="delivery_notes",
        lazy="selectin",
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dn_supplier_status", "supplier_id", "status"),
        Index("ix_dn_delivery_date", "delivery_date"),
        Index("ix_dn_reference_po", "reference_po_number"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote dn_number={self.dn_number}>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line item model."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dnl_delivery_note_line_number", "delivery_note_id", "line_number"),
        Index("ix_dnl_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine dn_id={self.delivery_note_id} line={self.line_number}>"


import uuid
