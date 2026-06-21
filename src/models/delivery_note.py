// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Table, Column

from app.database import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrderLine, PurchaseOrder


# Junction table for PO-DN lines many-to-many
purchase_order_delivery_note_lines = Table(
    "purchase_order_delivery_note_lines",
    Base.metadata,
    Column("purchase_order_line_id", String(36), ForeignKey("purchase_order_lines.id", ondelete="CASCADE"), primary_key=True),
    Column("delivery_note_line_id", String(36), ForeignKey("delivery_note_lines.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_po_dn_po_line", "purchase_order_line_id"),
    Index("ix_po_dn_dn_line", "delivery_note_line_id"),
)


class DeliveryNote(Base, BaseModel):
    """Delivery Note model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_supplier_dn_number", "supplier_code", "dn_number", unique=True),
        Index("ix_dn_status", "status"),
        Index("ix_dn_dn_date", "dn_date"),
    )

    dn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_reference: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="RECEIVED", nullable=False)  # RECEIVED, PARTIAL, COMPLETE
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(Base, BaseModel):
    """Delivery Note Line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dnl_dn_id_line_number", "delivery_note_id", "line_number", unique=True),
    )

    delivery_note_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship("DeliveryNote", back_populates="lines")
    matched_pos: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        secondary=purchase_order_delivery_note_lines,
        back_populates="matched_delivery_notes",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.item_code}>"

    @property
    def line_amount(self) -> Decimal:
        """Calculate line total."""
        return self.quantity_delivered * self.unit_price
