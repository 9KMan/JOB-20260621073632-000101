# models/balance_ledger.py
"""Balance Ledger model for tracking PO-to-Invoice balances."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger for tracking open balances between PO lines and Invoice lines.

    This table maintains a running balance of what has been invoiced vs. what
    has been delivered for each PO line.

    Attributes:
        po_line_id: Reference to the PO line
        invoice_line_id: Reference to the invoice line (optional)
        initial_quantity: Original PO line quantity
        delivered_quantity: Total quantity delivered
        invoiced_quantity: Total quantity invoiced
        matched_quantity: Total quantity matched
        open_quantity: Remaining open quantity
        initial_amount: Original PO line amount
        delivered_amount: Total delivered amount
        invoiced_amount: Total invoiced amount
        matched_amount: Total matched amount
        open_amount: Remaining open amount
        status: Balance status
        last_transaction_date: Date of last transaction
        notes: Additional notes
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_status", "status"),
        Index("ix_balance_ledger_open_quantity", "open_quantity"),
    )

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Quantity balances
    initial_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    open_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    # Amount balances
    initial_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    delivered_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    open_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.PENDING,
    )

    # Transaction tracking
    last_transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_transaction_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )
    invoice_line: Mapped["InvoiceLine"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger PO={self.po_line_id} Open={self.open_quantity}>"

    def update_balance(
        self,
        delivered_qty: Decimal | None = None,
        invoiced_qty: Decimal | None = None,
        matched_qty: Decimal | None = None,
        delivered_amt: Decimal | None = None,
        invoiced_amt: Decimal | None = None,
        matched_amt: Decimal | None = None,
        transaction_type: str | None = None,
    ) -> None:
        """Update balance quantities and amounts.

        Args:
            delivered_qty: Quantity delivered to add
            invoiced_qty: Quantity invoiced to add
            matched_qty: Quantity matched to add
            delivered_amt: Amount delivered to add
            invoiced_amt: Amount invoiced to add
            matched_amt: Amount matched to add
            transaction_type: Type of transaction
        """
        if delivered_qty is not None:
            self.delivered_quantity += delivered_qty
        if invoiced_qty is not None:
            self.invoiced_quantity += invoiced_qty
        if matched_qty is not None:
            self.matched_quantity += matched_qty
        if delivered_amt is not None:
            self.delivered_amount += delivered_amt
        if invoiced_amt is not None:
            self.invoiced_amount += invoiced_amt
        if matched_amt is not None:
            self.matched_amount += matched_amt

        # Recalculate open quantities
        self.open_quantity = (
            self.initial_quantity - self.delivered_quantity - self.matched_quantity
        )
        self.open_amount = (
            self.initial_amount - self.delivered_amount - self.matched_amount
        )

        # Update transaction tracking
        self.last_transaction_date = datetime.now(timezone.utc)
        if transaction_type:
            self.last_transaction_type = transaction_type

        # Update status based on open quantity
        if self.open_quantity <= 0:
            self.status = DocumentStatus.MATCHED
        elif self.open_quantity < self.initial_quantity:
            self.status = DocumentStatus.PARTIALLY_MATCHED
        else:
            self.status = DocumentStatus.PENDING

    @property
    def is_balanced(self) -> bool:
        """Check if the balance is fully matched (open = 0)."""
        return self.open_quantity <= 0 and self.open_amount <= 0

    @property
    def match_percentage(self) -> Decimal:
        """Calculate the percentage of matched quantity."""
        if self.initial_quantity == 0:
            return Decimal("100")
        return (self.matched_quantity / self.initial_quantity) * Decimal("100")
