// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.balance import BalanceLedger
    from src.models.match import Match


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line item model."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    item_code: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(length=500),
        nullable=False,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
    )
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
    )
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(length=20),
        nullable=True,
    )
    unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<DNLine {self.line_number}: {self.description}>"


class DeliveryNote(BaseModel):
    """Delivery Note model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
        String(length=50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        default="RECEIVED",
        index=True,
    )
    delivery_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(length=3),
        nullable=False,
        default="USD",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="delivery_notes",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number",
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
    )
    balance_entries: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"
