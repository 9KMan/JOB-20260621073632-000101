// src/models/delivery_note.py
"""Delivery Note model."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.balance import Balance
    from src.models.invoice import Invoice
    from src.models.match import Match
    from src.models.purchase_order import PurchaseOrder


class DeliveryNoteLine(BaseModel):
    """Individual line item in a Delivery Note."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    uom: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines"
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"


class DeliveryNote(BaseModel):
    """Delivery Note (GRN/Goods Receipt Note) model for 3-way matching."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    received_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    total_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="RECEIVED",
        nullable=False,
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number"
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes"
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="delivery_note"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        secondary="match_invoice_delivery_notes",
        back_populates="delivery_notes"
    )
    balances: Mapped[list["Balance"]] = relationship(
        "Balance",
        back_populates="delivery_note"
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"

    def calculate_totals(self) -> None:
        """Recalculate total quantity."""
        self.total_quantity = sum(line.quantity for line in self.lines)
