// src/app/models/delivery_note.py
"""Delivery Note models."""
import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel


class DeliveryNoteStatus(str, Enum):
    """Delivery Note status enumeration."""
    
    DRAFT = "draft"
    RECEIVED = "received"
    MATCHED = "matched"
    CLOSED = "closed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel):
    """Delivery Note header model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    po_reference: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default=DeliveryNoteStatus.DRAFT.value, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_records: Mapped[list["MatchRecord"]] = relationship(  # noqa: F821
        "MatchRecord",
        back_populates="delivery_note",
        foreign_keys="MatchRecord.delivery_note_id",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(dn_number={self.dn_number}, supplier={self.supplier_code})>"
    
    @property
    def is_open(self) -> bool:
        """Check if DN is open for matching."""
        return self.status in (DeliveryNoteStatus.RECEIVED.value,) and not self.is_archived


class DeliveryNoteLine(BaseModel):
    """Delivery Note line item model."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(line_number={self.line_number}, product={self.product_code})>"


from datetime import date
