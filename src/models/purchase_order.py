# src/models/purchase_order.py
"""Purchase Order model."""
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.matching import MatchingRecord


class PurchaseOrder(BaseModel):
    """Purchase Order model representing PO documents."""

    __tablename__ = "purchase_orders"

    po_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(String(100), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    po_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(50), default="open", nullable=False, index=True)
    notes = Column(String(1000), nullable=True)

    # Relationships
    line_items = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")
    delivery_notes = relationship("DeliveryNote", back_populates="purchase_order")
    matching_records = relationship("MatchingRecord", back_populates="purchase_order")


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=False)
    item_description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    line_amount = Column(Numeric(15, 2), nullable=False)
    uom = Column(String(20), nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
