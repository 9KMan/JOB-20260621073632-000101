// src/models/balance.py
// src/models/balance.py
"""Balance ledger model for tracking partial matches and balances."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class BalanceType(str, Enum):
    """Balance type enumeration."""
    PO_BALANCE = "po_balance"
    INVOICE_BALANCE = "invoice_balance"
    DELIVERY_BALANCE = "delivery_balance"


class BalanceStatus(str, Enum):
    """Balance status enumeration."""
    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    DISPUTED = "disputed"
    CLOSED = "closed"


class BalanceLedger(Base):
    """Balance ledger for tracking partial matches across documents."""

    __tablename__ = "balance_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Document reference
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(
        SQLEnum(BalanceType, name="balance_type_enum"),
        nullable=False,
    )
    
    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Status
    status: Mapped[BalanceStatus] = mapped_column(
        SQLEnum(BalanceStatus, name="balance_status_enum"),
        default=BalanceStatus.OPEN,
        nullable=False,
        index=True,
    )
    
    # Match references
    match_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Line item reference (for partial matches)
    line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    document = relationship(
        "Document",
        foreign_keys=[document_id],
    )
    match_result = relationship(
        "MatchResult",
        foreign_keys=[match_result_id],
    )
    line_item = relationship(
        "DocumentLineItem",
        foreign_keys=[line_item_id],
    )

    __table_args__ = (
        Index("ix_balance_ledger_document_status", "document_id", "status"),
        Index("ix_balance_ledger_type_status", "balance_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_number}:{self.remaining_amount}>"

    def to_dict(self) -> dict:
        """Convert balance ledger to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "document_type": self.document_type,
            "document_number": self.document_number,
            "balance_type": self.balance_type.value,
            "original_amount": str(self.original_amount),
            "matched_amount": str(self.matched_amount),
            "remaining_amount": str(self.remaining_amount),
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def update_balance(self, amount: Decimal) -> None:
        """Update balance with matched amount."""
        self.matched_amount += amount
        self.remaining_amount = self.original_amount - self.matched_amount
        
        if self.remaining_amount == Decimal("0.00"):
            self.status = BalanceStatus.FULLY_MATCHED
            self.closed_at = datetime.utcnow()
        elif self.matched_amount > Decimal("0.00"):
            self.status = BalanceStatus.PARTIALLY_MATCHED
