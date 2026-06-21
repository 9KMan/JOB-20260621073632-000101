// src/models/invoice.py
"""
FinaRo AP Automation Core Engine
Invoice Models
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.delivery_note import DeliveryNote
    from app.models.match import Match


class Invoice(BaseModel):
    """
    Invoice model representing an incoming vendor invoice.
    Part of the 3-way matching process.
    """
    __tablename__ = "invoices"
    
    # Invoice Identification
    invoice_number = Column(String(50), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True, index=True)
    
    # Reference Information
    po_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    supplier_invoice_number = Column(String(100), nullable=True, index=True)
    
    # Invoice Dates
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    received_date = Column(Date, default=date.today, nullable=False)
    
    # Invoice Status
    status = Column(
        SQLEnum(
            'RECEIVED', 'PENDING_REVIEW', 'MATCHED', 'APPROVED',
            'REJECTED', 'DISPUTED', 'PAID', 'CANCELLED',
            name='invoice_status'
        ),
        default='RECEIVED',
        nullable=False,
        index=True
    )
    
    # Financial
    currency = Column(String(3), default='USD', nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Tax Information
    tax_id = Column(String(50), nullable=True)
    tax_rate = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    
    # Payment Terms
    payment_terms = Column(String(100), nullable=True)
    payment_method = Column(String(50), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    department = Column(String(100), nullable=True, index=True)
    
    # OCR/Raw Data
    raw_ocr_data = Column(Text, nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    
    # Relationships
    po: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        lazy="selectin"
    )
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="invoice",
        foreign_keys="Match.invoice_id",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number='{self.invoice_number}', status='{self.status}')>"
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate balance due on the invoice."""
        return self.total_amount - self.amount_paid
    
    @property
    def is_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.balance_due <= Decimal('0.00')


class InvoiceLine(BaseModel):
    """
    Invoice Line Item model.
    Represents individual line items within an Invoice.
    """
    __tablename__ = "invoice_lines"
    
    # Foreign Key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Line Identification
    line_number = Column(Integer, nullable=False)
    internal_reference = Column(String(100), nullable=True)
    
    # Product/Service Information
    product_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    product_code = Column(String(50), nullable=True, index=True)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Quantities
    quantity_invoiced = Column(Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    
    # Unit of Measure
    unit_of_measure = Column(String(20), default='EA', nullable=False)
    
    # Pricing
    unit_price = Column(Numeric(15, 4), nullable=False, default=Decimal('0.0000'))
    line_total = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    tax_rate = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Matched Quantities
    quantity_matched = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    
    # Status
    status = Column(
        SQLEnum(
            'PENDING', 'PARTIAL', 'MATCHED', 'DISPUTED',
            name='invline_status'
        ),
        default='PENDING',
        nullable=False,
        index=True
    )
    
    # Relationship
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, invoice_id={self.invoice_id}, line_number={self.line_number})>"
    
    @property
    def quantity_unmatched(self) -> Decimal:
        """Calculate unmatched quantity."""
        return self.quantity_invoiced - self.quantity_matched
    
    @property
    def amount_unmatched(self) -> Decimal:
        """Calculate unmatched amount."""
        return self.line_total - (self.unit_price * self.quantity_matched)
    
    def calculate_totals(self) -> None:
        """Calculate line totals based on quantity and unit price."""
        self.line_total = self.quantity_invoiced * self.unit_price
        self.tax_amount = self.line_total * self.tax_rate
