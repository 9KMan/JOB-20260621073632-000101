// src/models/balance.py
// src/models/balance.py
"""Balance Ledger model for tracking partial matches and balances."""

import uuid
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from models.base import BaseModel


class BalanceType(str, Enum):
    """Types of balances in the ledger."""
    
    INVOICE = "INVOICE"
    DELIVERY = "DELIVERY"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class BalanceStatus(str, Enum):
    """Status of a balance entry."""
    
    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    CLOSED = "CLOSED"


class BalanceLedger(Base, BaseModel):
    """
    Balance Ledger for tracking partial matches and balances across all three document types.
    
    This enables the system to handle:
    - Partial shipments
    - Split invoices
    - Multi-delivery scenarios
    """

    __tablename__ = "balance_ledger"

    # Balance type and status
    balance_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=BalanceStatus.OPEN.value, index=True)
    
    # Document reference
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PO, Invoice, DN
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    line_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Balance amounts
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Quantity tracking
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0"))
    balance_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    
    # Reference dates
    document_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Link to parent balance if split
    parent_balance_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledger.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Match history
    match_ids: Mapped[Optional[list]] = mapped_column(
        # Using JSON to store multiple match references
        nullable=True,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_number} - {self.balance_type} - {self.balance_amount}>"
