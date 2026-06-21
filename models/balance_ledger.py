# models/balance_ledger.py
"""Balance Ledger model for tracking PO/Invoice balances."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import MatchDecision

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(TimestampMixin, UUIDPrimaryKeyMixin, Base):
    """Balance Ledger for tracking open/closed balances per PO line.

    This table maintains running balances for each PO line, tracking
    what has been delivered, invoiced, and paid. It enables the
    matching engine to make decisions based on cumulative values.
    """

    __tablename__ = "balance_ledger"

    # References
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    """Type of balance: 'ordered', 'delivered', 'invoiced', 'paid'"""

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    amount_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Calculated balances
    balance_qty_open: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    """Open quantity = ordered - delivered - invoiced - paid"""
    balance_amount_open: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    """Open amount = ordered_amount - delivered - invoiced - paid"""

    # Status
    is_balanced: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    is_over_delivered: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    is_over_invoiced: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Transaction reference
    last_transaction_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    last_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    last_transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger_entries",
    )

    __table_args__ = (
        UniqueConstraint("po_line_id", "balance_type", name="uq_balance_ledger_line_type"),
        Index("ix_balance_ledger_po", "po_id"),
        Index("ix_balance_ledger_po_line", "po_line_id"),
        Index("ix_balance_ledger_balanced", "is_balanced"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger PO:{self.po_id} Line:{self.po_line_id} Type:{self.balance_type}>"

    def calculate_open_balance(self) -> tuple[Decimal, Decimal]:
        """Calculate open quantity and amount.

        Returns:
            Tuple of (open_qty, open_amount)
        """
        open_qty = (
            self.quantity_ordered
            - self.quantity_delivered
            - self.quantity_invoiced
            - self.quantity_paid
        )
        open_amount = (
            self.amount_ordered
            - self.amount_delivered
            - self.amount_invoiced
            - self.amount_paid
        )
        return open_qty, open_amount

    def update_from_transaction(
        self,
        transaction_type: str,
        transaction_id: uuid.UUID,
        quantity: Decimal,
        amount: Decimal,
        transaction_date: datetime | None = None,
    ) -> None:
        """Update balance from a transaction.

        Args:
            transaction_type: Type of transaction ('invoice', 'payment', etc.)
            transaction_id: ID of the transaction
            quantity: Quantity delta
            amount: Amount delta
            transaction_date: When the transaction occurred
        """
        if transaction_type == "invoice":
            self.quantity_invoiced += quantity
            self.amount_invoiced += amount
        elif transaction_type == "payment":
            self.quantity_paid += quantity
            self.amount_paid += amount
        elif transaction_type == "delivery":
            self.quantity_delivered += quantity
            self.amount_delivered += amount

        self.last_transaction_type = transaction_type
        self.last_transaction_id = transaction_id
        self.last_transaction_date = transaction_date or datetime.now()

        self.balance_qty_open, self.balance_amount_open = self.calculate_open_balance()
        self.is_balanced = self.balance_qty_open == 0 and self.balance_amount_open == 0
        self.is_over_delivered = self.quantity_delivered > self.quantity_ordered
        self.is_over_invoiced = self.quantity_invoiced > self.quantity_ordered


__all__ = ["BalanceLedger"]
