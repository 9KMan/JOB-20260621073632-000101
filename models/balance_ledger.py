# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

Tracks running balances for purchase order lines to enable
partial invoice matching and payment tracking.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin, TableNameMixin
from models.enums import BalanceType


class BalanceLedger(Base, UUIDMixin, TimestampMixin, TableNameMixin):
    """Balance ledger for tracking PO line balances.

    Maintains running balances for:
    - Invoice amounts matched against PO lines
    - Credit memos
    - Payments
    - Adjustments

    This enables partial matching and accurate outstanding balance tracking.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "transaction_type",
            "transaction_id",
            name="uq_balance_ledger_transaction",
        ),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_transaction_id", "transaction_id"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[BalanceType] = mapped_column(
        String(50),
        nullable=False,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.transaction_type}: "
            f"{self.amount} (balance: {self.balance_after})>"
        )
