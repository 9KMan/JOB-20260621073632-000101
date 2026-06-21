// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Date, DateTime, Numeric, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, BaseModel

if TYPE_CHECKING:
    from src.models.vendor import Vendor
    from src.models.match import Match
    from src.models.balance import Balance


class DeliveryNote(Base, BaseModel):
    """Delivery Note/Warehouse Receipt model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    po_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    received_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    attachments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        back_populates="delivery_notes"
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan"
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="delivery_note"
    )
    balances: Mapped[list["Balance"]] = relationship(
        "Balance",
        back_populates="delivery_note"
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number})>"


class DeliveryNoteLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Delivery Note Line item model."""
    
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
    item_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    condition: Mapped[str] = mapped_column(
        String(50),
        default="good",
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, item={self.item_code}, qty={self.quantity_delivered})>"


# Import func for server_default
from sqlalchemy import func
