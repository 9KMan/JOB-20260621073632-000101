// src/models/balance.py
"""Balance tracking models for partial matches and split scenarios."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrderLine
    from app.models.invoice import InvoiceLine
    from app.models.delivery_note import DeliveryNoteLine


class BalanceLedger(Base, BaseModel):
    """Balance ledger for tracking outstanding amounts across documents."""

    __tablename__ = "balance_ledgers"
    __table_args__ = (
        Index("ix_bl_document_type_document_id", "document_type", "document_id"),
        Index("ix_bl_po_line_id", "po_line_id"),
    )

    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # INVOICE, DELIVERY_NOTE
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    po_line_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("purchase_order_lines.id"), nullable=True)

    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Quantity tracking
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)  # OPEN, PARTIAL, CLOSED
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship("PurchaseOrderLine")
    entries: Mapped[list["BalanceEntry"]] = relationship(
        "BalanceEntry",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}:{self.document_id}>"

    @property
    def is_balanced(self) -> bool:
        """Check if ledger is fully balanced."""
        return self.remaining_amount == Decimal("0.00") and self.remaining_quantity == Decimal("0.00")


class BalanceEntry(Base, BaseModel):
    """Individual balance entry for tracking match history."""

    __tablename__ = "balance_entries"
    __table_args__ = (
        Index("ix_be_ledger_id", "ledger_id"),
        Index("ix_be_match_id", "match_id"),
    )

    ledger_id: Mapped[str] = mapped_column(String(36), ForeignKey("balance_ledgers.id", ondelete="CASCADE"), nullable=False)
    match_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Entry details
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)  # MATCH, REVERSAL, ADJUSTMENT
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    ledger: Mapped["BalanceLedger"] = relationship("BalanceLedger", back_populates="entries")

    def __repr__(self) -> str:
        return f"<BalanceEntry {self.entry_type}: {self.amount}>"
