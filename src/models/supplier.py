// src/models/supplier.py
"""Supplier model definition."""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier entity representing vendors in the system."""
    
    __tablename__ = "suppliers"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    invoices = relationship("Invoice", back_populates="supplier")
    delivery_notes = relationship("DeliveryNote", back_populates="supplier")
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name={self.name}, code={self.code})>"
