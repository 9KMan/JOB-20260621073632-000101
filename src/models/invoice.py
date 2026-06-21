# src/models/invoice.py
"""Invoice model."""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.match_result import MatchResult
    from src.models.balance_ledger import BalanceLedger


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model for AP processing."""
    
    __tablename__ = "invoices"
    
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    po_reference = Column(String(50), nullable=True, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    status = Column(
        String(20),
        default="PENDING",
        nullable=False,
        index=True,
    )  # PENDING, MATCHED, APPROVED, PAID, DISPUTED, REJECTED
    
    notes = Column(Text, nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Relationships
    line_items = relationship(
        "InvoiceLineItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matched_pos = relationship(
        "MatchResult",
        foreign_keys="MatchResult.invoice_id",
        back_populates="invoice",
    )
    balance_entries = relationship(
        "BalanceLedger",
        foreign_keys="BalanceLedger.invoice_id",
        back_populates="invoice",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"


class InvoiceLineItem(Base, UUIDMixin, TimestampMixin):
    """Invoice Line Item model."""
    
    __tablename__ = "invoice_line_items"
    
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    line_number = Column(String(10), nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<InvoiceLineItem(id={self.id}, sku={self.sku})>"
