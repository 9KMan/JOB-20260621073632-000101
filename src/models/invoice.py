# src/models/invoice.py
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    RECEIVED = "received"
    MATCHED = "matched"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(BaseModel):
    """Invoice model - one of the documents in 3-way matching."""

    __tablename__ = "invoices"

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    po_reference = Column(String(50), nullable=True, index=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    amount_paid = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(String(1000), nullable=True)
    metadata = Column(String(5000), nullable=True)

    # Relationships
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    matching_results = relationship("MatchingResult", back_populates="invoice")


class InvoiceLine(BaseModel):
    """Invoice Line Item model."""

    __tablename__ = "invoice_lines"

    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(50), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_amount = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    po_line_reference = Column(String(36), ForeignKey("purchase_order_lines.id"), nullable=True)
    notes = Column(String(500), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    matched_po_line = relationship("PurchaseOrderLine", foreign_keys=[po_line_reference])
