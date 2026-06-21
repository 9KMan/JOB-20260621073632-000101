// src/models/supplier.py
"""Supplier model for vendor management."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier model representing vendors/suppliers."""

    __tablename__ = "suppliers"

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
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
        Text,
        nullable=True,
    )
    tax_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    payment_terms: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    bank_details: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="supplier",
        lazy="selectin",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="supplier",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Supplier code={self.code} name={self.name}>"
