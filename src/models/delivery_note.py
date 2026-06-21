// src/models/delivery_note.py
"""Delivery Note models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.matching import MatchRecord
    from src.models.balance import BalanceLedger


class DeliveryNote(BaseModel, SoftDeleteMixin):
    """Delivery Note - One of the three documents in 3-way matching."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    po_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RECEIVED"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    
    received_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number"
    )
    
    match_records: Mapped[list["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="delivery_note"
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(BaseModel):
    """Individual line item in a Delivery Note."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0")
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.sku}>"
