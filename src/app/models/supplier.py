# src/app/models/supplier.py
"""Supplier model."""
import uuid
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote


class Supplier(BaseModel):
    """Supplier/Vendor model."""
    
    __tablename__ = "suppliers"
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Relationships
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        foreign_keys="PurchaseOrder.supplier_id",
    )
    
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="supplier",
        foreign_keys="Invoice.supplier_id",
    )
    
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="supplier",
        foreign_keys="DeliveryNote.supplier_id",
    )
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, code={self.code}, name={self.name})>"
