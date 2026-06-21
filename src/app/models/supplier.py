// src/app/models/supplier.py
"""
Supplier model.
"""
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Supplier(Base, UUIDPrimaryKey, TimestampMixin):
    """Supplier/Vendor model."""

    __tablename__ = "suppliers"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    invoices = relationship("Invoice", back_populates="supplier")
    delivery_notes = relationship("DeliveryNote", back_populates="supplier")

    def __repr__(self) -> str:
        return f"<Supplier {self.code}: {self.name}>"
