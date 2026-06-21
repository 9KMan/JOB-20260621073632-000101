// models/delivery_note.py
"""Delivery Note model."""

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
    from models.purchase_order import PurchaseOrder


class DeliveryNote(Base, BaseModel):
    """Delivery Note model — matched against PO in Layer 2."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    po_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="delivery_notes")
    created_by_user: Mapped["User"] = relationship("User", back_populates="delivery_notes")
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(Base, BaseModel):
    """Delivery Note Line Item."""

    __tablename__ = "delivery_note_lines"

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
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
    delivery_note: Mapped["DeliveryNote"] = relationship("DeliveryNote", back_populates="lines")

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.item_code}>"


import uuid
