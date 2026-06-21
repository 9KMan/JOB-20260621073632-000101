// models/balance_ledger.py
"""BalanceLedger — financial balance tracking per PO line."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryMixin
from models.enums import MatchDecision

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder, POLine


class BalanceLedger(Base, UUIDPrimaryMixin, TimestampMixin):
    """
    Balance ledger entry — tracks invoiced vs. delivered vs. received amounts
    per PO line to enforce quantity and value controls.

    Schema:
      debit  = amount invoiced  (positive)
      credit = amount paid     (positive)
      balance = SUM(debits) - SUM(credits)

    The ledger is append-only; corrections are made via a new row with a
    negative debit (or positive credit).
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_po_id", "po_id"),
        UniqueConstraint("po_line_id", "invoice_id", name="uq_balance_ledger_po_invoice"),
        CheckConstraint(
            "entry_type IN ('debit', 'credit', 'adjustment')",
            name="ck_balance_ledger_entry_type",
        ),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    entry_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="'debit' | 'credit' | 'adjustment'"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Running balance snapshot (denormalised for query performance)
    running_balance_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    running_balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="balance_entries"
    )
    po_line: Mapped["POLine"] = relationship(
        "POLine", back_populates="balance_entries"
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice", back_populates="balance_entries"
    )
