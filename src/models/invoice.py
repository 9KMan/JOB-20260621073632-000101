// src/models/invoice.py
"""Invoice and Invoice Line models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class InvoiceStatus(str):
    """Invoice status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHING = "matching"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class InvoiceType(str):
    """Invoice type enum."""
    STANDARD = "standard"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"


class Invoice(BaseModel):
    """Invoice model - one of the three documents in 3-way matching."""

    __tablename__ = "invoices"

    invoice_number: str = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id: str = Column(String(100), nullable=False, index=True)
    supplier_name: str = Column(String(255), nullable=False)
    supplier_code: Optional[str] = Column(String(50), nullable=True)

    invoice_date: date = Column(Date, nullable=False)
    due_date: Optional[date] = Column(Date, nullable=True)
    received_date: date = Column(Date, default=date.today, nullable=False)

    invoice_type: str = Column(String(20), default=InvoiceType.STANDARD, nullable=False)
    status: str = Column(String(20), default=InvoiceStatus.SUBMITTED, nullable=False)

    po_reference: Optional[str] = Column(String(50), nullable=True, index=True)
    po_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)

    currency: str = Column(String(3), default="USD", nullable=False)
    subtotal: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    paid_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    payment_terms: Optional[str] = Column(String(100), nullable=True)
    payment_reference: Optional[str] = Column(String(100), nullable=True)

    notes: Optional[str] = Column(Text, nullable=True)
    rejection_reason: Optional[str] = Column(Text, nullable=True)

    created_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(BaseModel):
    """Invoice Line item model."""

    __tablename__ = "invoice_lines"

    invoice_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    line_number: int = Column(Integer, nullable=False)
    item_code: str = Column(String(50), nullable=False)
    item_description: str = Column(String(500), nullable=False)
    quantity: Decimal = Column(Numeric(15, 4), nullable=False)
    unit_of_measure: str = Column(String(20), default="EA", nullable=False)
    unit_price: Decimal = Column(Numeric(15, 4), nullable=False)
    line_amount: Decimal = Column(Numeric(15, 2), nullable=False)
    tax_code: Optional[str] = Column(String(20), nullable=True)
    tax_rate: Decimal = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    tax_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Link to PO line for matching
    po_line_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True)
    matched_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    po_line = relationship("PurchaseOrderLine", foreign_keys=[po_line_id])

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.item_code}>"
