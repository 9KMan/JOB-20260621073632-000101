// src/models/delivery_note.py
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
import enum
from src.models.base import BaseModel


class DeliveryNoteStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel):
    __tablename__ = "delivery_notes"
    
    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_code = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(DeliveryNoteStatus), default=DeliveryNoteStatus.SUBMITTED, nullable=False)
    delivery_date = Column(Date, nullable=False)
    received_by = Column(String(255), nullable=True)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    
    purchase_order = relationship("PurchaseOrder", back_populates="delivery_notes")
    lines = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="delivery_note")


class DeliveryNoteLine(BaseModel):
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(50), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    delivery_note = relationship("DeliveryNote", back_populates="lines")
