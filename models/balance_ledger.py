# models/balance_ledger.py
"""Balance ledger model for tracking PO/Invoice balances."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger for tracking purchase order balances."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
    )

    po_line_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    running_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    running_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.transaction_type} - Qty: {self.quantity_change}>"


class TransactionType:
    """Transaction type constants."""

    PO_CREATED = "po_created"
    PO_AMENDED = "po_amended"
    DN_RECEIVED = "dn_received"
    DN_CANCELLED = "dn_cancelled"
    INVOICE_CREATED = "invoice_created"
    INVOICE_MATCHED = "invoice_matched"
    INVOICE_CANCELLED = "invoice_cancelled"
    CREDIT_MEMO = "credit_memo"
    ADJUSTMENT = "adjustment"
