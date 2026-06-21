// src/models/balance.py
"""Balance tracking model for 3-way matching."""
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base

if TYPE_CHECKING:
    from src.models.document import Document


class BalanceType(str, Enum):
    """Types of balance entries."""
    DEBIT = "debit"
    CREDIT = "credit"


class Balance(UUIDMixin, Base):
    """
    Balance ledger for tracking amounts across documents.
    Used for partial matches, split invoices, and multi-delivery scenarios.
    """
    
    __tablename__ = "balances"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "balance_type", name="uq_document_balance_type"
        ),
    )
    
    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(
        nullable=False,
    )
    
    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
    )
    
    @property
    def open_amount(self) -> Decimal:
        """Calculate open (unmatched) amount."""
        return self.original_amount - self.matched_amount
    
    @property
    def is_fully_matched(self) -> bool:
        """Check if balance is fully matched."""
        return self.matched_amount >= self.original_amount
    
    # Reference to related document
    reference_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reference_document_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    match_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[document_id],
        back_populates="balances",
    )
    reference_document: Mapped[Optional["Document"]] = relationship(
        "Document",
        foreign_keys=[reference_document_id],
    )
    
    def __repr__(self) -> str:
        return f"<Balance {self.document_id}:{self.balance_type.value}={self.open_amount}>"


import uuid
from datetime import date
from decimal import Decimal
