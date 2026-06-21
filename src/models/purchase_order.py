# src/models/purchase_order.py
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from src.models.base import BaseModel


class POStatus(str, enum.Enum):
    """Purchase Order status enumeration."""
    DRAFT = "draft"
    OPEN = "open"
    PARTIALLY_RECEIVED = "partially_received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor in 3-way matching."""

    __tablename__ = "purchase_orders"

    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    status = Column(SQLEnum(POStatus), default=POStatus.DRAFT, nullable=False, index=True)
    currency = Column(String(3), default="USD", nullable=False)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(String(1000), nullable=True)
    metadata = Column(String(5000), nullable=True)  # JSON string for additional data

    # Relationships
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    matched_invoices = relationship("MatchingResult", foreign_keys="MatchingResult.po_id", back_populates="purchase_order")
    matched_delivery_notes = relationship("MatchingResult", foreign_keys="MatchingResult.dn_id", back_populates="purchase_order")


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(50), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_amount = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    notes = Column(String(500), nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
