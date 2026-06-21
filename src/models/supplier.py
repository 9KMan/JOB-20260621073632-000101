// src/models/supplier.py
"""Supplier model."""
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier/vendor model."""

    __tablename__ = "suppliers"

    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    purchase_orders = relationship(
        "PurchaseOrder", back_populates="supplier", lazy="dynamic"
    )
    invoices = relationship(
        "Invoice", back_populates="supplier", lazy="dynamic"
    )
    delivery_notes = relationship(
        "DeliveryNote", back_populates="supplier", lazy="dynamic"
    )
