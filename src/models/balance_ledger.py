// src/models/balance_ledger.py
"""Balance ledger model for tracking partial matches and balances."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class BalanceType(str, Enum):
    """Type of balance entry."""
    INVOICE_BALANCE = "invoice_balance"
    DELIVERY_BALANCE = "delivery_balance"
    PO_BALANCE = "po_balance"
    PARTIAL_MATCH = "partial_match"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"


class BalanceDirection(str, Enum):
    """Direction of the balance."""
    DEBIT = "debit"
    CREDIT = "credit"


class BalanceStatus(str, Enum):
    """Status of the balance entry."""
    OPEN = "open"
    PARTIALLY_RESOLVED = "partially_resolved"
    RESOLVED = "resolved"
    WRITE_OFF = "write_off"
    DISPUTED = "disputed"


class BalanceLedger(BaseModel):
    """Balance ledger model - tracks balances across all document types."""

    __tablename__ = "balance_ledger"

    # Balance type and direction
    balance_type: str = Column(String(30), nullable=False)
    direction: str = Column(String(10), nullable=False)
    status: str = Column(String(20), default=BalanceStatus.OPEN.value, nullable=False)

    # Source document reference
    source_document_type: str = Column(String(20), nullable=False)  # invoice, delivery_note, purchase_order
    source_document_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    source_line_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), nullable=True)

    # Related document reference
    related_document_type: Optional[str] = Column(String(20), nullable=True)
    related_document_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), nullable=True)

    # Balance amounts
    original_amount: Decimal = Column(Numeric(15, 2), nullable=False)
    balance_amount: Decimal = Column(Numeric(15, 2), nullable=False)
    resolved_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    currency: str = Column(String(3), default="USD", nullable=False)

    # Match reference
    matching_record_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("matching_records.id"), nullable=True)

    # Resolution details
    resolution_type: Optional[str] = Column(String(50), nullable=True)
    resolution_notes: Optional[str] = Column(Text, nullable=True)
    resolved_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Reference to original transaction for tracking
    transaction_reference: Optional[str] = Column(String(100), nullable=True)
    notes: Optional[str] = Column(Text, nullable=True)

    # Relationships
    matching_record = relationship("MatchingRecord", foreign_keys=[matching_record_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.id} - {self.balance_type} - {self.balance_amount}>"
