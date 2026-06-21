# src/models/delivery_note.py
"""Delivery Note model."""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.match_result import MatchResult


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model for goods receipt tracking."""
    
    __tablename__ = "delivery_notes"
    
    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    po_reference = Column(String(50), nullable=True, index=True)
    invoice_reference = Column(String(50), nullable=True, index=True)
    delivery_date = Column(Date, nullable=False)
    
    currency = Column(String(3), default="USD", nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    status = Column(
        String(20),
        default="RECEIVED",
        nullable=False,
        index=True,
    )  # RECEIVED, PARTIALLY_MATCHED, MATCHED, CANCELLED
    
    notes = Column(Text, nullable=True)
    carrier_name = Column(String(255), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    
    # Relationships
    line_items = relationship(
        "DeliveryNoteLineItem",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    matched_pos = relationship(
        "MatchResult",
        foreign_keys="MatchResult.delivery_note_id",
        back_populates="delivery_note",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number})>"


class DeliveryNoteLineItem(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""
    
    __tablename__ = "delivery_note_line_items"
    
    delivery_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    line_number = Column(String(10), nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    
    quantity_delivered = Column(Numeric(15, 3), nullable=False)
    quantity_accepted = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    quantity_rejected = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLineItem(id={self.id}, sku={self.sku})>"
