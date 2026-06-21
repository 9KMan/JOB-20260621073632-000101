# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking quantities and amounts."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import BalanceType

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import POLine
    from models.delivery_note import DeliveryNoteLine


class BalanceLedger(UUIDMixin, TimestampMixin, Base):
    """Balance Ledger model for tracking expected vs actual quantities.

    This table maintains the running balance of quantities and amounts
    for each PO line, delivery note line, and invoice line to enable
    matching and variance analysis.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_delivery_line_id", "delivery_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_balance_type", "balance_type"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
        Index("ix_balance_ledger_source_id_type", "source_type", "source_id"),
    )

    po_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    balance_type: Mapped[BalanceType] = mapped_column(String(20), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    po_line: Mapped["POLine | None"] = relationship(
        "POLine", back_populates="balance_ledger_entries"
    )
    delivery_note_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine", back_populates="balance_ledger_entries"
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine", back_populates="balance_ledger_entries"
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.balance_type}: {self.quantity} @ {self.amount}>"

    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount (quantity * unit_price)."""
        if self.unit_price is not None:
            return self.quantity * self.unit_price
        return self.amount
