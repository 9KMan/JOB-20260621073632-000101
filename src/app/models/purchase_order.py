// src/app/models/purchase_order.py
"""
Purchase Order Model
PO header and line items for 3-way matching.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Date, Numeric, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PurchaseOrder(BaseModel):
    """Purchase Order header."""
    
    __tablename__ = "purchase_orders"
    
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
        index=True,
    )
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item."""
    
    __tablename__ = "purchase_order_lines"
    
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"
