// src/app/models/supplier.py
"""Supplier model definition."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from src.app.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier entity for accounts payable."""

    __tablename__ = "suppliers"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    purchase_orders = relationship(
        "PurchaseOrder", back_populates="supplier", lazy="dynamic"
    )
    invoices = relationship("Invoice", back_populates="supplier", lazy="dynamic")
    delivery_notes = relationship(
        "DeliveryNote", back_populates="supplier", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, code={self.code}, name={self.name})>"
