// src/models/balance.py
"""Balance Ledger for tracking partial matches and balances."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder


class BalanceLedger(BaseModel):
    """
    Balance Ledger - Tracks partial matches and running balances.
    
    Transaction Types:
    - INVOICE_CREATED: Invoice amount added to ledger
    - INVOICE_MATCHED: Invoice amount reduced by match
    - DELIVERY_CREATED: Delivery amount added
    - DELIVERY_MATCHED: Delivery amount reduced by match
    - PARTIAL_MATCH: Partial amount matched
    - DISPUTE: Amount moved to dispute
    - ADJUSTMENT: Manual adjustment
    """
    
    __tablename__ = "balance_ledger"
    
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )
    
    reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}: {self.transaction_type} = {self.amount}>"
