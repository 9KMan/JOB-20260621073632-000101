# models/balance_ledger.py
"""Balance Ledger model for tracking open balances."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.purchase_order import POLine


class BalanceLedger(Base, UUIDPrimaryKey, TimestampMixin):
    """Balance ledger for tracking PO line balances and invoicing."""

    __tablename__ = "balance_ledger"

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Original PO amounts
    po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    po_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    po_line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Current balance tracking
    delivered_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    delivered_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    invoiced_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    invoiced_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    paid_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    # Computed balances
    open_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    open_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Last activity
    last_invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    is_balanced: Mapped[bool] = mapped_column(default=False)
    balance_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    po_line: Mapped["POLine"] = relationship("POLine", back_populates="balance_ledger")

    __table_args__ = (
        Index("ix_balance_ledger_po", "po_line_id"),
        Index("ix_balance_ledger_open", "open_quantity", "open_amount"),
    )

    def calculate_open_balance(self) -> tuple[Decimal, Decimal]:
        """
        Calculate open quantity and amount.

        Returns:
            tuple: (open_quantity, open_amount)
        """
        delivered_qty = self.delivered_quantity or Decimal("0")
        invoiced_qty = self.invoiced_quantity or Decimal("0")
        paid_qty = self.paid_quantity or Decimal("0")

        open_qty = delivered_qty - paid_qty
        open_qty = max(open_qty, Decimal("0"))

        if self.po_unit_price and open_qty > 0:
            open_amt = open_qty * self.po_unit_price
        else:
            open_amt = self.open_amount

        return open_qty, open_amt

    def update_balance(
        self,
        delivered_qty: Decimal | None = None,
        invoiced_qty: Decimal | None = None,
        paid_qty: Decimal | None = None,
        invoice_date: date | None = None,
        payment_date: date | None = None,
    ) -> None:
        """
        Update balance quantities.

        Args:
            delivered_qty: Additional delivered quantity
            invoiced_qty: Additional invoiced quantity
            paid_qty: Additional paid quantity
            invoice_date: Date of invoice
            payment_date: Date of payment
        """
        if delivered_qty is not None:
            self.delivered_quantity += delivered_qty
            self.delivered_amount = self.delivered_quantity * self.po_unit_price

        if invoiced_qty is not None:
            self.invoiced_quantity += invoiced_qty
            self.invoiced_amount = self.invoiced_quantity * self.po_unit_price
            if invoice_date:
                self.last_invoice_date = invoice_date

        if paid_qty is not None:
            self.paid_quantity += paid_qty
            self.paid_amount = self.paid_quantity * self.po_unit_price
            if payment_date:
                self.last_payment_date = payment_date

        self.open_quantity, self.open_amount = self.calculate_open_balance()
        self.is_balanced = self.open_quantity <= Decimal("0")
        if self.is_balanced:
            self.balance_date = date.today()
