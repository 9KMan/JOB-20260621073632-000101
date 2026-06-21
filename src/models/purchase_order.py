// src/models/purchase_order.py
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
import enum
from src.models.base import BaseModel


class POStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    __tablename__ = "purchase_orders"
    
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_code = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    status = Column(SQLEnum(POStatus), default=POStatus.SUBMITTED, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(String(1000), nullable=True)
    
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")
    delivery_notes = relationship("DeliveryNote", back_populates="purchase_order")
    matches = relationship("Match", back_populates="purchase_order")


class PurchaseOrderLine(BaseModel):
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(50), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
