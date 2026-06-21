# src/models/delivery_note.py
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery Note model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    subtotal: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="RECEIVED", nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign Keys
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="delivery_notes")
    line_items = relationship("DeliveryNoteLineItem", back_populates="delivery_note", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLineItem(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""
    
    __tablename__ = "delivery_note_line_items"
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity_delivered: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLineItem {self.line_number}: {self.item_code}>"
