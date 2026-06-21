// src/app/models/balance.py
"""Balance and BalanceTransaction models for tracking partial matches."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Date, DateTime, Numeric, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.base import BaseModel


class BalanceType(str, enum.Enum):
    """Balance type enumeration."""
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    PURCHASE_ORDER = "purchase_order"


class TransactionType(str, enum.Enum):
    """Balance transaction type enumeration."""
    DEBIT = "debit"
    CREDIT = "credit"


class Balance(BaseModel):
    """
    Balance model for tracking partial matches and outstanding balances
    across all three document types.
    """
    
    __tablename__ = "balances"
    __table_args__ = (
        Index("ix_balances_document_type_id", "document_type", "document_id"),
        Index("ix_balances_supplier_id", "supplier_id"),
        Index("ix_balances_status", "status"),
    )
    
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    
    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    document_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    supplier = relationship("Supplier")
    transactions = relationship(
        "BalanceTransaction",
        back_populates="balance",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Balance {self.document_type}:{self.document_number}>"


class BalanceTransaction(BaseModel):
    """
    Balance transaction model for tracking balance changes.
    """
    
    __tablename__ = "balance_transactions"
    __table_args__ = (
        Index("ix_balance_transactions_balance_id", "balance_id"),
        Index("ix_balance_transactions_match_id", "match_id"),
    )
    
    balance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balances.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    transaction_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    # Relationships
    balance = relationship("Balance", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<BalanceTransaction {self.balance_id}:{self.transaction_type}>"
