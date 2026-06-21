// src/models/balance.py
"""Balance ledger for tracking partial matches and resolutions."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.match import Match


class BalanceLedger(BaseModel):
    """Master ledger for tracking open balances across all document types."""

    __tablename__ = "balance_ledgers"
    __table_args__ = (
        Index("ix_balance_ledgers_document_type_document_id", "document_type", "document_id", unique=True),
        Index("ix_balance_ledgers_supplier_id", "supplier_id"),
        Index("ix_balance_ledgers_status", "status"),
    )

    # Document reference
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # invoice, delivery_note, purchase_order
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Balance tracking
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    open_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
        index=True,
    )  # open, partial, resolved, cancelled

    # Reference document
    reference_document_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reference_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    entries: Mapped[list["BalanceEntry"]] = relationship(
        back_populates="ledger",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, doc={self.document_type}:{self.document_id})>"

    def update_balance(self, matched: Decimal) -> None:
        """Update the matched and open amounts."""
        self.matched_amount += matched
        self.open_amount = self.original_amount - self.matched_amount
        if self.open_amount <= Decimal("0.01"):  # Handle floating point
            self.status = "resolved"


class BalanceEntry(BaseModel):
    """Individual balance entry for tracking match transactions."""

    __tablename__ = "balance_entries"
    __table_args__ = (
        Index("ix_balance_entries_ledger_id", "ledger_id"),
        Index("ix_balance_entries_match_id", "match_id"),
    )

    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledgers.id", ondelete="CASCADE"),
        nullable=False,
    )

    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Entry details
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)  # match, reversal, adjustment, write_off
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    ledger: Mapped["BalanceLedger"] = relationship(back_populates="entries")

    def __repr__(self) -> str:
        return f"<BalanceEntry(id={self.id}, type={self.entry_type}, amount={self.amount})>"
