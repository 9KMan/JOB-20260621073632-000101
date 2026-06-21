// src/models/supplier.py
"""Supplier model for vendor management."""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class Supplier(BaseModel):
    """Supplier/vendor model."""
    
    __tablename__ = "suppliers"
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    contact_email: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    
    contact_phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )
    
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    
    tax_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    # Relationships
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        lazy="dynamic"
    )
    
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="supplier",
        lazy="dynamic"
    )
    
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="supplier",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, code={self.code}, name={self.name})>"
