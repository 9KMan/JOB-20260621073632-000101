// src/models/supplier.py
"""Supplier model."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier/vendor model."""
    
    __tablename__ = "suppliers"
    
    code: Mapped[str] = mapped_column(
        String(length=50),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(length=255),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
    )
    payment_terms_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="supplier",
    )
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="supplier",
    )
    cross_references: Mapped[List["CrossReference"]] = relationship(
        "CrossReference",
        back_populates="supplier",
    )
    
    def __repr__(self) -> str:
        return f"<Supplier {self.code}: {self.name}>"
