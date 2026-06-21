// src/models/balance.py
"""Balance tracking for partial matches and splits."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class BalanceLedger(Base):
    """Balance ledger for tracking partial matches across documents."""
    
    __tablename__ = "balance_ledger"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Document reference
    document_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Balance tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    pending_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Status
    balance_status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        nullable=False,
        index=True,
    )  # OPEN, PARTIAL, CLOSED
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Relationships
    entries = relationship("BalanceLedgerEntry", back_populates="balance_ledger", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, document={self.document_type}:{self.document_number}, balance_status={self.balance_status})>"


class BalanceLedgerEntry(Base):
    """Individual entries in the balance ledger."""
    
    __tablename__ = "balance_ledger_entries"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    balance_ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reference_document_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reference_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    reference_document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    balance_ledger = relationship("BalanceLedger", back_populates="entries")
    
    def __repr__(self) -> str:
        return f"<BalanceLedgerEntry(id={self.id}, entry_type={self.entry_type}, amount={self.amount})>"
