// src/models/delivery_note.py
from sqlalchemy import Column, String, Numeric, Date, Integer, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery Note status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeliveryNote(BaseModel):
    """Delivery Note model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    delivery_date = Column(Date, nullable=False)
    received_date = Column(Date, nullable=True)
    
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD", nullable=False)
    
    status = Column(Enum(DeliveryNoteStatus), default=DeliveryNoteStatus.DRAFT, nullable=False, index=True)
    
    matched_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    
    notes = Column(Text, nullable=True)
    carrier_info = Column(String(255), nullable=True)
    
    # Relationships
    line_items = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")
    matched_po = relationship("PurchaseOrder", back_populates="delivery_notes")
    matches = relationship("Match", back_populates="delivery_note")
    balance_entries = relationship("BalanceEntry", back_populates="delivery_note")
    
    def __repr__(self):
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line Item model."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True, index=True)
    
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="line_items")
    matched_po_line = relationship("PurchaseOrderLine", back_populates="delivery_note_lines")
    invoice_lines = relationship("InvoiceLine", back_populates="matched_dn_line")
    
    def __repr__(self):
        return f"<DeliveryNoteLine {self.line_number}>"
