// src/models/purchase_order.py
"""Purchase Order models."""
from decimal import Decimal
from typing import List

from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class POStatus(str, enum.Enum):
    """Purchase Order status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """Purchase Order header."""

    __tablename__ = "purchase_orders"

    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    status = Column(SQLEnum(POStatus), default=POStatus.SUBMITTED, nullable=False, index=True)
    order_date = Column(Text, nullable=False)  # ISO date string
    expected_delivery_date = Column(Text, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_invoices = relationship(
        "MatchRecord",
        foreign_keys="MatchRecord.po_id",
        back_populates="purchase_order",
        lazy="dynamic",
    )


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item."""

    __tablename__ = "purchase_order_lines"

    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    line_total = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_rate = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    expected_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    received_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
