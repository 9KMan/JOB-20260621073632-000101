// src/app/models/balance.py
"""Balance Ledger models for tracking partial matches."""
import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel


class BalanceType(str, Enum):
    """Balance type enumeration."""
    
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    PURCHASE_ORDER = "purchase_order"


class BalanceStatus(str, Enum):
    """Balance status enumeration."""
    
    OPEN = "open"
    PARTIAL = "partial"
    CLOSED = "closed"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"


class BalanceLedger(BaseModel):
    """Balance Ledger for tracking partial matches and balances."""
    
    __tablename__ = "balance_ledger"
    
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    balance_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default=BalanceStatus.OPEN.value, nullable=False)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(doc_type={self.document_type}, doc_id={self.document_id}, balance={self.balance_amount})>"
    
    @property
    def is_balanced(self) -> bool:
        """Check if the balance is fully matched."""
        return self.balance_amount == Decimal("0.00") and self.balance_quantity == Decimal("0.000")
    
    @property
    def balance_percentage(self) -> Decimal:
        """Calculate balance percentage."""
        if self.original_amount == Decimal("0.00"):
            return Decimal("100.00")
        return (self.balance_amount / self.original_amount) * Decimal("100.00")


from decimal import Decimal
