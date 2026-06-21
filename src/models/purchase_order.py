// src/models/purchase_order.py
from sqlalchemy import Column, String, Numeric, Date, Integer, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class POStatus(str, enum.Enum):
    """Purchase Order status enumeration."""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(BaseModel):
    """Purchase Order model - single source of truth for anchoring."""
    
    __tablename__ = "purchase_orders"
    
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD", nullable=False)
    
    status = Column(Enum(POStatus), default=POStatus.DRAFT, nullable=False, index=True)
    
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    
    # Relationships
    line_items = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="matched_po")
    delivery_notes = relationship("DeliveryNote", back_populates="matched_po")
    matches = relationship("Match", back_populates="purchase_order")
    
    def __repr__(self):
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item model."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    expected_delivery_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    invoice_lines = relationship("InvoiceLine", back_populates="matched_po_line")
    delivery_note_lines = relationship("DeliveryNoteLine", back_populates="matched_po_line")
    
    def __repr__(self):
        return f"<PurchaseOrderLine {self.line_number}>"
