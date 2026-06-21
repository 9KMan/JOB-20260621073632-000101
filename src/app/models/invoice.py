// src/app/models/invoice.py
"""
Invoice and Invoice Line models.
"""
from decimal import Decimal
from datetime import date
from typing import List

from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin


class Invoice(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Invoice header (from supplier)."""

    __tablename__ = "invoices"

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    po_reference = Column(String(50), nullable=True, index=True)  # Reference to PO
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, matched, approved, paid, disputed
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Payment info
    payment_status = Column(String(50), default="unpaid", nullable=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # ERP Integration
    erp_reference = Column(String(100), nullable=True, index=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    lines = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    match_results = relationship(
        "MatchResult",
        foreign_keys="MatchResult.invoice_id",
        back_populates="invoice",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"

    @property
    def is_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.payment_status == "paid" and self.paid_amount >= self.total_amount


class InvoiceLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Invoice line item."""

    __tablename__ = "invoice_lines"

    invoice_id = Column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.product_code}>"
