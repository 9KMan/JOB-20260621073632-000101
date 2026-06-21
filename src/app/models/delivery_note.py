// src/app/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Date, Numeric, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel


class DeliveryNote(BaseModel):
    """Delivery Note / Goods Receipt model - one of the three documents in 3-way matching."""
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_supplier_dn_number", "supplier_id", "dn_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
    )
    
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
    )
    
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    po_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    received_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    total_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    open_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Relationships
    supplier = relationship("Supplier", back_populates="delivery_notes")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    lines = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    match = relationship("Match", back_populates="delivery_note", uselist=False)
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(BaseModel):
    """Line item on a Delivery Note."""
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
    )
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )
    
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    po_line = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        foreign_keys=[po_line_id],
    )
    invoice_lines = relationship(
        "InvoiceLine",
        back_populates="dn_line",
        foreign_keys="InvoiceLine.dn_line_id",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.delivery_note_id}:{self.line_number}>"
