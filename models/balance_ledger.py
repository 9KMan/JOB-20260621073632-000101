// models/balance_ledger.py
"""Balance Ledger model for tracking PO/Invoice balances."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import LineStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger tracks remaining balances for PO lines."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_as_of_date", "as_of_date"),
    )

    # Foreign keys
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Balance amounts
    original_po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    original_po_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    delivered_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"))
    delivered_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    invoiced_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"))
    invoiced_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    paid_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    
    # Calculated balances
    remaining_po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    remaining_po_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
    )
    
    # Date tracking
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_transaction_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Transaction reference
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger",
    )

    def calculate_remaining_balance(self) -> tuple[Decimal, Decimal]:
        """Calculate remaining quantity and amount."""
        remaining_qty = self.original_po_quantity - self.invoiced_quantity
        remaining_amt = self.original_po_amount - self.invoiced_amount
        return max(remaining_qty, Decimal("0.00")), max(remaining_amt, Decimal("0.00"))

    def update_balance(
        self,
        quantity_delta: Decimal,
        amount_delta: Decimal,
        transaction_type: str,
        transaction_ref: str | None = None,
    ) -> None:
        """Update balance with a new transaction."""
        self.invoiced_quantity += quantity_delta
        self.invoiced_amount += amount_delta
        self.remaining_po_quantity, self.remaining_po_amount = self.calculate_remaining_balance()
        self.last_transaction_date = datetime.utcnow()
        self.transaction_type = transaction_type
        self.transaction_ref = transaction_ref
        
        # Update status based on remaining balance
        if self.remaining_po_quantity <= Decimal("0.00"):
            self.status = LineStatus.FULLY_MATCHED
        elif self.invoiced_quantity > Decimal("0.00"):
            self.status = LineStatus.PARTIALLY_MATCHED
