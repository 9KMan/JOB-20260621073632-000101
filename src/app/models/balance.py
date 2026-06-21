// src/app/models/balance.py
"""
Balance Ledger Model
Tracks balances across all document types for partial match resolution.
"""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BalanceLedger(BaseModel):
    """
    Balance ledger for tracking partial matches and balances.
    This enables handling of:
    - Partial shipments
    - Split invoices
    - Multi-delivery scenarios
    """
    
    __tablename__ = "balance_ledger"
    
    # Reference to the transaction that created this balance
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # 'invoice', 'delivery_note', 'adjustment'
    
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Reference document
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'PO', 'invoice', 'DN'
    
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Balance details
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'quantity', 'amount'
    
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    applied_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    applied_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Status
    is_settled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    settled_at: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger {self.transaction_type}: {self.remaining_amount}>"
