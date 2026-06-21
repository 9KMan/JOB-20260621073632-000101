// src/app/models/supplier.py
"""Supplier model."""

import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier/Vendor model."""
    
    __tablename__ = "suppliers"
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    
    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )
    
    tax_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    
    payment_terms: Mapped[str] = mapped_column(
        String(100),
        default="Net 30",
        nullable=False,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    invoices = relationship("Invoice", back_populates="supplier")
    delivery_notes = relationship("DeliveryNote", back_populates="supplier")
    
    def __repr__(self) -> str:
        return f"<Supplier {self.code}: {self.name}>"
