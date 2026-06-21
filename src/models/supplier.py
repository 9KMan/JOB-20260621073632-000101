// src/models/supplier.py
"""Supplier model."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class Supplier(BaseModel, SoftDeleteMixin):
    """Supplier/vendor model."""

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
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="supplier",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="supplier",
    )

    def __repr__(self) -> str:
        return f"<Supplier {self.code}: {self.name}>"
