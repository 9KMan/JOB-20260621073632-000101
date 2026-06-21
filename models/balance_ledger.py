# models/balance_ledger.py
"""BalanceLedger and LedgerTransaction SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, BaseMixin
from models.enums import LedgerTransactionType


class BalanceLedger(Base, BaseMixin):
    """Balance Ledger for tracking open balances per PO line."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_vendor_id", "vendor_id"),
        Index("ix_balance_ledger_balance_date", "balance_date"),
        UniqueConstraint(
            "po_line_id",
            "invoice_id",
            "transaction_type",
            name="uq_balance_ledger_po_invoice_txn",
        ),
    )

    # PO Line Reference
    po_line_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # PO Reference (for quick access)
    po_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vendor Reference
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Invoice Reference (optional for non-invoice transactions)
    invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Transaction Information
    transaction_type: Mapped[LedgerTransactionType] = mapped_column(
        Enum(LedgerTransactionType, name="ledger_transaction_type", create_type=False),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    # Amounts
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Running Balance
    running_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    running_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Balance Date (for period-end reporting)
    balance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    is_reconciled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    reconciled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Additional Data
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.id} po_line={self.po_line_id} amount={self.amount}>"
