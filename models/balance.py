// models/balance.py
// models/balance.py
"""Balance Ledger models for tracking partial matches and balances."""
import uuid
from decimal import Decimal
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Date, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from models.base import BaseModel


class BalanceType(enum.Enum):
    """Balance type for tracking."""
    INVOICE_BALANCE = "invoice_balance"
    PO_BALANCE = "po_balance"
    DELIVERY_BALANCE = "delivery_balance"


class BalanceLedger(BaseModel):
    """Balance ledger for tracking remaining balances across documents."""
    
    __tablename__ = "balance_ledger"
    
    # Document reference
    document_type = Column(String(50), nullable=False)  # PO, INVOICE, DN
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_number = Column(String(100), nullable=False)
    
    # Line reference (optional)
    line_id = Column(UUID(as_uuid=True), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Balance tracking
    balance_type = Column(String(50), nullable=False)  # From BalanceType
    original_quantity = Column(Numeric(15, 3), nullable=False)
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    remaining_quantity = Column(Numeric(15, 3), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    
    # Status
    is_settled = Column(String(20), default="OPEN", nullable=False)
    settlement_date = Column(Date, nullable=True)
    
    # Metadata
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier")
    entries = relationship("BalanceEntry", back_populates="balance_ledger", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('document_type', 'document_id', 'line_id', name='uq_balance_document_line'),
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, document_type={self.document_type}, document_number={self.document_number})>"
    
    def update_balance(self, quantity: Decimal, amount: Decimal):
        """Update matched and remaining balances."""
        self.matched_quantity += quantity
        self.matched_amount += amount
        self.remaining_quantity = self.original_quantity - self.matched_quantity
        self.remaining_amount = self.original_amount - self.matched_amount
        
        if self.remaining_quantity <= 0 and self.remaining_amount <= 0:
            self.is_settled = "SETTLED"
        else:
            self.is_settled = "PARTIAL"


class BalanceEntry(BaseModel):
    """Individual balance entry for audit trail."""
    
    __tablename__ = "balance_entries"
    
    balance_ledger_id = Column(UUID(as_uuid=True), ForeignKey("balance_ledger.id", ondelete="CASCADE"), nullable=False)
    matching_record_id = Column(UUID(as_uuid=True), ForeignKey("matching_records.id", ondelete="SET NULL"), nullable=True)
    
    # Entry details
    entry_type = Column(String(50), nullable=False)  # INITIAL, MATCH, REVERSE
    quantity_change = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    amount_change = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Running balance
    quantity_before = Column(Numeric(15, 3), nullable=False)
    quantity_after = Column(Numeric(15, 3), nullable=False)
    amount_before = Column(Numeric(15, 2), nullable=False)
    amount_after = Column(Numeric(15, 2), nullable=False)
    
    # Reference
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    balance_ledger = relationship("BalanceLedger", back_populates="entries")
    
    def __repr__(self) -> str:
        return f"<BalanceEntry(id={self.id}, balance_ledger_id={self.balance_ledger_id}, entry_type={self.entry_type})>"
