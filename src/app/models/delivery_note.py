// src/app/models/delivery_note.py
"""
Delivery Note Model
Goods received notes for 3-way matching.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Date, Numeric, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DeliveryNote(BaseModel):
    """Delivery Note/Goods Receipt header."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="received",
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="delivery_notes")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note line item."""
    
    __tablename__ = "delivery_note_lines"
    
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    condition: Mapped[str] = mapped_column(
        String(20),
        default="good",
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"
