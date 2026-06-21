// src/models/invoice.py
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
import enum
from src.models.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHED = "matched"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(BaseModel):
    __tablename__ = "invoices"
    
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_code = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.SUBMITTED, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="invoice")


class InvoiceLine(BaseModel):
    __tablename__ = "invoice_lines"
    
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(50), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="lines")
