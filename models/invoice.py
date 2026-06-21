// models/invoice.py
"""Invoice models."""
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from models.base import BaseModel


class InvoiceStatus(enum.Enum):
    """Invoice status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class Invoice(BaseModel):
    """Invoice model."""
    
    __tablename__ = "invoices"
    
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default=InvoiceStatus.SUBMITTED.value, nullable=False, index=True)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    
    # Totals
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    matched_records = relationship("MatchingRecord", foreign_keys="MatchingRecord.invoice_id", back_populates="invoice")
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, supplier_id={self.supplier_id})>"
    
    def calculate_totals(self):
        """Recalculate totals from lines."""
        self.subtotal = sum(line.line_total for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        self.total_amount = self.subtotal + self.tax_amount


class InvoiceLine(BaseModel):
    """Invoice Line Item model."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    matched_lines = relationship("MatchingLine", back_populates="invoice_line")
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, invoice_id={self.invoice_id}, line_number={self.line_number})>"
    
    def calculate_totals(self):
        """Calculate line totals based on quantity and unit price."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * (self.tax_rate / 100)
