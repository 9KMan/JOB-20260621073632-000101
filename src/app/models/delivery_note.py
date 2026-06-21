// src/app/models/delivery_note.py
"""Delivery Note model."""
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.user import User


class DeliveryNote(BaseModel):
    """Delivery Note model - third document in 3-way matching."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_date: Mapped[date] = mapped_column(
        nullable=False,
    )
    received_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="RECEIVED",
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        back_populates="delivery_notes",
    )
    created_by_user: Mapped["User | None"] = relationship(
        back_populates="delivery_notes",
        foreign_keys=[created_by],
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    matches: Mapped[list["MatchResult"]] = relationship(
        back_populates="delivery_note",
        foreign_keys="MatchResult.delivery_note_id",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line Item."""

    __tablename__ = "delivery_note_lines"

    dn_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    item_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}>"
