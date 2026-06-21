// src/models/supplier.py
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier model for vendor management."""
    
    __tablename__ = "suppliers"
    
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA", nullable=True)
    
    tax_id = Column(String(50), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder")
    invoices = relationship("Invoice")
    delivery_notes = relationship("DeliveryNote")
    
    def __repr__(self):
        return f"<Supplier {self.supplier_code}>"
