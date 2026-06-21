// src/models/vendor.py
"""Vendor model for suppliers."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class Vendor(Base, BaseModel):
    """Vendor/Supplier model."""
    
    __tablename__ = "vendors"
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    tax_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )
    country: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )
    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    payment_terms_days: Mapped[int] = mapped_column(
        default=30,
        nullable=False
    )
    bank_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    bank_account: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="vendor"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="vendor"
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="vendor"
    )
    
    def __repr__(self) -> str:
        return f"<Vendor(id={self.id}, code={self.code}, name={self.name})>"
