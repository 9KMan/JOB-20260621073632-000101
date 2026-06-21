// models/purchase_order.py
"""Purchase Order model."""

from decimal import Decimal
from typing import List, TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNote


class PurchaseOrder(Base, BaseModel):
    """Purchase Order model — single source of truth in Layer 1."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    created_by_user: Mapped["User"] = relationship("User", back_populates="purchase_orders")
    lines: Mapped[List["POLine"]] = relationship(
        "POLine", 
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="purchase_order")
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship("DeliveryNote", back_populates="purchase_order")

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class POLine(Base, BaseModel):
    """Purchase Order Line Item."""

    __tablename__ = "po_lines"

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")

    def __repr__(self) -> str:
        return f"<POLine {self.line_number}: {self.item_code}>"


import uuid
