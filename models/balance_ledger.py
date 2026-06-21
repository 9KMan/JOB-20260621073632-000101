# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

Tracks running balances for purchase order lines to support
invoice matching and validation.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger for tracking PO line balances.

    Maintains running balances for quantity ordered, received,
    invoiced, and paid per purchase order line.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_reference_type", "reference_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )

    # References
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reference_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Balance snapshot
    balance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Timestamps
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Description
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.reference_number} - {self.transaction_type}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount to be paid."""
        return self.amount_ordered - self.amount_paid


__all__ = [
    "BalanceLedger",
]
