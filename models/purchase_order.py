// models/purchase_order.py
"""Purchase Order models."""
import uuid
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor for 3-way matching."""
    
    __tablename__ = "purchase_orders"
    
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    status = Column(String(50), default="OPEN", nullable=False, index=True)  # OPEN, PARTIAL, CLOSED, CANCELLED
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    
    # Totals (computed from lines)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    matched_invoices = relationship("MatchingRecord", foreign_keys="MatchingRecord.po_id", back_populates="purchase_order")
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, supplier_id={self.supplier_id})>"
    
    def calculate_totals(self):
        """Recalculate totals from lines."""
        self.subtotal = sum(line.line_total for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        self.total_amount = self.subtotal + self.tax_amount


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item model."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    matched_lines = relationship("MatchingLine", back_populates="po_line")
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, po_id={self.purchase_order_id}, line_number={self.line_number})>"
    
    def calculate_totals(self):
        """Calculate line totals based on quantity and unit price."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * (self.tax_rate / 100)
