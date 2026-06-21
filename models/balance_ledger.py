# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import LedgerTransactionType

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance ledger for tracking PO line quantities and amounts."""

    __tablename__ = "balance_ledger"

    # Reference to PO Line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document Reference
    document_type: Mapped[LedgerTransactionType] = mapped_column(
        LedgerTransactionType,
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    document_number: Mapped[str] = mapped_column(String(100), nullable=False)
    document_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Transaction Details
    transaction_type: Mapped[LedgerTransactionType] = mapped_column(
        LedgerTransactionType,
        nullable=False,
    )
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    amount_change: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Running Balance (after this transaction)
    running_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    running_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Status
    is_reconciled: Mapped[bool] = mapped_column(default=False, nullable=False)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledgers",
    )

    __table_args__ = (
        Index("ix_ledger_po_document", "purchase_order_id", "document_type"),
        Index("ix_ledger_running", "po_line_id", "running_quantity"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}: {self.quantity_change} @ {self.running_quantity}>"

    def reconcile(self) -> None:
        """Mark this ledger entry as reconciled."""
        self.is_reconciled = True
        self.reconciled_at = datetime.now(timezone.utc)
