// src/app/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Date, Numeric, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor document in 3-way matching."""
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_supplier_po_number", "supplier_id", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
    )
    
    po_number: Mapped[str] = mapped_column(
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
    
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    shipping_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
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
    supplier = relationship("Supplier", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    invoice_matches = relationship("Match", back_populates="purchase_order")
    delivery_note_matches = relationship(
        "Match",
        back_populates="purchase_order",
        foreign_keys="Match.purchase_order_id",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(BaseModel):
    """Line item on a Purchase Order."""
    
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
    )
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
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
        nullable=False,
    )
    
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    open_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    delivery_note_lines = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys="DeliveryNoteLine.po_line_id",
    )
    invoice_lines = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.purchase_order_id}:{self.line_number}>"
