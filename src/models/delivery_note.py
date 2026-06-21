// src/models/delivery_note.py
"""Delivery Note models."""
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TimestampMixin


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel, TimestampMixin):
    """Delivery note model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    po_reference: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    
    delivery_date: Mapped[str] = mapped_column(String(10), nullable=False)
    received_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        SQLEnum(DeliveryNoteStatus, name="dn_status", create_type=False),
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
    )
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(BaseModel, TimestampMixin):
    """Delivery note line item model."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    delivery_note: Mapped["DeliveryNote"] = relationship(
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"
