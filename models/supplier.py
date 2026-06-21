// models/supplier.py
"""Supplier model for vendor management."""
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class Supplier(BaseModel):
    """Supplier/vendor model."""
    
    __tablename__ = "suppliers"
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), nullable=True, index=True)
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    payment_terms_days = Column(String(100), nullable=True)  # e.g., "Net 30"
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    invoices = relationship("Invoice", back_populates="supplier")
    delivery_notes = relationship("DeliveryNote", back_populates="supplier")
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, code={self.code}, name={self.name})>"
