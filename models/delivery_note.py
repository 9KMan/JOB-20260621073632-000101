// models/delivery_note.py
"""Delivery Note models."""
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from models.base import BaseModel


class DeliveryNoteStatus(enum.Enum):
    """Delivery Note status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    COMPLETE = "complete"
    PARTIAL = "partial"


class DeliveryNote(BaseModel):
    """Delivery Note / Goods Receipt model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    delivery_date = Column(Date, nullable=False)
    received_by = Column(String(255), nullable=True)
    status = Column(String(50), default=DeliveryNoteStatus.SUBMITTED.value, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="delivery_notes")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    lines = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")
    matched_records = relationship("MatchingRecord", foreign_keys="MatchingRecord.dn_id", back_populates="delivery_note")
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, supplier_id={self.supplier_id})>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line Item model."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    quantity_ordered = Column(Numeric(15, 3), nullable=True)  # From PO
    quantity_delivered = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    po_line = relationship("PurchaseOrderLine", foreign_keys=[po_line_id])
    matched_lines = relationship("MatchingLine", back_populates="dn_line")
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, dn_id={self.delivery_note_id}, line_number={self.line_number})>"
