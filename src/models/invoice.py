// src/models/invoice.py
"""
Invoice model
One side of the 3-way match
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from decimal import Decimal

from src.models.base import UUIDModel, TimestampModel, SoftDeleteModel


class Invoice(UUIDModel, TimestampModel, SoftDeleteModel):
    """Invoice model"""
    __tablename__ = "invoices"
    
    # Business identifiers
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    # Reference to PO (set during matching)
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id"),
        nullable=True,
        index=True
    )
    
    # Dates
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Amounts
    subtotal = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status tracking
    STATUS_PENDING = "pending"
    STATUS_MATCHED = "matched"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PAID = "paid"
    STATUS_DISPUTED = "disputed"
    
    status = Column(String(50), default=STATUS_PENDING, nullable=False, index=True)
    
    # Payment info
    payment_terms = Column(String(100), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Line items
    line_items = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    # Relationships
    invoice = relationship(
        "PurchaseOrder",
        back_populates="invoices"
    )
    created_by_user = relationship(
        "User",
        back_populates="created_invoices",
        foreign_keys=[created_by]
    )
    match_records = relationship(
        "MatchRecord",
        back_populates="invoice"
    )
    balance_records = relationship(
        "BalanceLedger",
        back_populates="invoice"
    )
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(UUIDModel, TimestampModel):
    """Line items for Invoice"""
    __tablename__ = "invoice_lines"
    
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    line_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    tax_rate = Column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    
    # Link to PO line (optional, set during matching)
    purchase_order_line_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id"),
        nullable=True
    )
    
    # Relationship
    invoice = relationship(
        "Invoice",
        back_populates="line_items"
    )
    
    def __repr__(self):
        return f"<InvoiceLine {self.line_number} - {self.description}>"
