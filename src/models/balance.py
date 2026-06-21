// src/models/balance.py
// src/models/balance.py
"""
FinaRo AP Automation Core Engine
Balance Ledger Models for Tracking Partial Matches
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from app.models.invoice import Invoice, InvoiceLine
    from app.models.delivery_note import DeliveryNote, DeliveryNoteLine


class BalanceType(str, Enum):
    """Balance type enumeration."""
    PO_OPEN = "PO_OPEN"
    INVOICE_OPEN = "INVOICE_OPEN"
    DN_OPEN = "DN_OPEN"
    VARIANCE = "VARIANCE"
    CREDIT = "CREDIT"


class BalanceDirection(str, Enum):
    """Balance direction enumeration."""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class BalanceLedger(BaseModel):
    """
    Balance Ledger model for tracking balances across documents.
    Enables handling of partial shipments, split invoices, and multi-delivery scenarios.
    """
    __tablename__ = "balance_ledger"
    
    # Ledger Identification
    ledger_number = Column(String(50), nullable=False, index=True)
    
    # Document References
    document_type = Column(String(20), nullable=False, index=True)  # PO, Invoice, DN
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_number = Column(String(50), nullable=False, index=True)
    
    # Line References (nullable for header-level balances)
    line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    line_number = Column(String(10), nullable=True)
    
    # Balance Type
    balance_type = Column(
        String(20),
        default=BalanceType.PO_OPEN.value,
        nullable=False,
        index=True
    )
    direction = Column(
        String(10),
        default=BalanceDirection.DEBIT.value,
        nullable=False
    )
    
    # Product Information
    product_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    product_code = Column(String(50), nullable=True)
    product_name = Column(String(255), nullable=True)
    
    # Quantities
    original_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    matched_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    remaining_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    
    # Amounts
    original_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    remaining_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Status
    status = Column(
        String(20),
        default='OPEN',
        nullable=False,
        index=True
    )
    
    # Reference to related balance (for credits, reversals, etc.)
    related_balance_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Match Reference
    match_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Currency
    currency = Column(String(3), default='USD', nullable=False)
    
    # Effective Date
    effective_date = Column(Date, nullable=False, index=True)
    maturity_date = Column(Date, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Resolution
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, ledger_number='{self.ledger_number}', remaining_amount={self.remaining_amount})>"
    
    def update_balance(self, matched_qty: Decimal, matched_amt: Decimal) -> None:
        """
        Update the balance after a match.
        
        Args:
            matched_qty: Quantity being matched
            matched_amt: Amount being matched
        """
        self.matched_quantity += matched_qty
        self.matched_amount += matched_amt
        self.remaining_quantity = self.original_quantity - self.matched_quantity
        self.remaining_amount = self.original_amount - self.matched_amount
        
        # Update status based on remaining balance
        if self.remaining_amount <= Decimal('0.00'):
            self.status = 'CLOSED'
        elif self.remaining_amount < self.original_amount:
            self.status = 'PARTIAL'
    
    def reverse_balance(self, qty: Decimal, amt: Decimal, notes: str) -> None:
        """
        Create a reversal entry for this balance.
        
        Args:
            qty: Quantity to reverse
            amt: Amount to reverse
            notes: Reason for reversal
        """
        # This would typically create a new balance entry with opposite direction
        # For simplicity, we just update the current record
        self.matched_quantity -= qty
        self.matched_amount -= amt
        self.remaining_quantity = self.original_quantity - self.matched_quantity
        self.remaining_amount = self.original_amount - self.matched_amount
        
        if self.remaining_amount > Decimal('0.00'):
            self.status = 'OPEN'
        
        self.notes = f"{self.notes or ''}\nReversal: {notes}"
    
    @property
    def is_closed(self) -> bool:
        """Check if balance is fully closed."""
        return self.status == 'CLOSED' and self.remaining_amount <= Decimal('0.00')
    
    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate how much of the balance has been utilized."""
        if self.original_amount > 0:
            return (self.matched_amount / self.original_amount) * 100
        return Decimal('0.00')
