// src/models/delivery_note.py
"""Delivery Note models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.models.invoice import Invoice, InvoiceLine
    from src.models.match import Match


class DeliveryNote(BaseModel, SoftDeleteMixin):
    """Delivery Note / Goods Received Note (GRN)."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_supplier_dn_number", "supplier_id", "dn_number", unique=True),
        Index("ix_delivery_notes_supplier_id", "supplier_id"),
        Index("ix_delivery_notes_purchase_order_id", "purchase_order_id"),
        Index("ix_delivery_notes_status", "status"),
    )

    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    received_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, matched, closed

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(default=None)

    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(back_populates="delivery_notes")
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[list["Match"]] = relationship(back_populates="delivery_note")

    @property
    def unmatched_amount(self) -> Decimal:
        """Calculate unmatched amount."""
        return self.total_amount - self.matched_amount

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number})>"


class DeliveryNoteLine(BaseModel):
    """Line item in a Delivery Note."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
    )

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Reference to PO line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(back_populates="lines")

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, sku={self.sku}, qty={self.quantity})>"
