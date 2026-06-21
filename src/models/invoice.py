// src/models/invoice.py
from sqlalchemy import Column, String, Numeric, Date, Integer, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    PAID = "PAID"


class Invoice(BaseModel):
    """Invoice model."""
    
    __tablename__ = "invoices"
    
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD", nullable=False)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    
    matched_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    
    notes = Column(Text, nullable=True)
    payment_terms = Column(String(255), nullable=True)
    
    # Relationships
    line_items = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    matched_po = relationship("PurchaseOrder", back_populates="invoices")
    matches = relationship("Match", back_populates="invoice")
    balance_entries = relationship("BalanceEntry", back_populates="invoice")
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(BaseModel):
    """Invoice Line Item model."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True, index=True)
    matched_dn_line_id = Column(UUID(as_uuid=True), ForeignKey("delivery_note_lines.id", ondelete="SET NULL"), nullable=True, index=True)
    
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    matched_po_line = relationship("PurchaseOrderLine", back_populates="invoice_lines")
    matched_dn_line = relationship("DeliveryNoteLine", back_populates="invoice_lines")
    
    def __repr__(self):
        return f"<InvoiceLine {self.line_number}>"
