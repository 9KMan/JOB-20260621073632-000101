# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance Ledger model tracking quantities and amounts per PO line.

    This table maintains a running balance for each purchase order line,
    tracking what's been ordered, received, invoiced, and paid.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id", unique=True),
        Index("ix_balance_ledger_last_transaction", "last_transaction_at"),
        {
            "schema": None,
        },
    )

    # Reference to PO Line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
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

    # Calculated Balances (stored for query performance)
    quantity_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    amount_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Over-delivery tracking
    over_delivery_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )
    over_delivery_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Last transaction tracking
    last_transaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    last_transaction_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )

    def recalculate_balances(self) -> None:
        """Recalculate all balance fields."""
        self.quantity_balance = (
            self.quantity_ordered - self.quantity_invoiced
        )
        self.amount_balance = self.amount_ordered - self.amount_invoiced

        # Track over-delivery
        if self.quantity_received > self.quantity_ordered:
            self.over_delivery_quantity = (
                self.quantity_received - self.quantity_ordered
            )
            self.over_delivery_amount = (
                self.over_delivery_quantity * (self.amount_ordered / self.quantity_ordered)
                if self.quantity_ordered > 0
                else Decimal("0")
            )

    def record_invoice(
        self,
        quantity: Decimal,
        amount: Decimal,
        transaction_type: str,
    ) -> None:
        """Record an invoice against this balance.

        Args:
            quantity: Quantity invoiced
            amount: Amount invoiced
            transaction_type: Type of transaction
        """
        self.quantity_invoiced += quantity
        self.amount_invoiced += amount
        self.last_transaction_at = datetime.now(timezone.utc)
        self.last_transaction_type = transaction_type
        self.recalculate_balances()

    def record_payment(
        self,
        quantity: Decimal,
        amount: Decimal,
    ) -> None:
        """Record a payment against this balance.

        Args:
            quantity: Quantity paid
            amount: Amount paid
        """
        self.quantity_paid += quantity
        self.amount_paid += amount
        self.last_transaction_at = datetime.now(timezone.utc)
        self.last_transaction_type = "payment"

    def record_receipt(
        self,
        quantity: Decimal,
    ) -> None:
        """Record a receipt against this balance.

        Args:
            quantity: Quantity received
        """
        self.quantity_received += quantity
        self.last_transaction_at = datetime.now(timezone.utc)
        self.last_transaction_type = "receipt"
        self.recalculate_balances()

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if fully invoiced."""
        return self.quantity_invoiced >= self.quantity_ordered

    @property
    def is_fully_paid(self) -> bool:
        """Check if fully paid."""
        return self.amount_paid >= self.amount_ordered

    @property
    def invoice_percentage(self) -> Decimal:
        """Calculate invoice percentage."""
        if self.quantity_ordered == 0:
            return Decimal("0")
        return (self.quantity_invoiced / self.quantity_ordered) * Decimal("100")

    @property
    def payment_percentage(self) -> Decimal:
        """Calculate payment percentage."""
        if self.amount_ordered == 0:
            return Decimal("0")
        return (self.amount_paid / self.amount_ordered) * Decimal("100")

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger(id={self.id}, po_line_id={self.po_line_id}, "
            f"qty_balance={self.quantity_balance})>"
        )
