# models/balance_ledger.py
"""Balance Ledger — tracks running balances for PO lines against invoices and delivery notes."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Per-PO-line balance ledger tracking invoiced vs. delivered amounts.

    This table provides a real-time view of open balances per PO line,
    enabling the matching engine to determine how much of a PO line
    is still available for matching.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_dn_line_id", "dn_line_id"),
        Index(
            "ix_balance_ledger_po_line_invoice",
            "po_line_id",
            "invoice_id",
            unique=True,
        ),
    )

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Invoice reference
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Delivery Note reference
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Amounts tracked
    po_quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )

    # Running balance (positive = still open, zero = fully matched)
    quantity_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )

    # Financial amounts
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0")
    )
    amount_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0")
    )

    # Status
    is_closed: Mapped[bool] = mapped_column(default=False)
    closed_at: Mapped[Date | None] = mapped_column(Date, nullable=True)

    transaction_type: Mapped[str] = mapped_column(
        String(30),
        default="invoice",
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger po_line={self.po_line_id} "
            f"qty_balance={self.quantity_balance}>"
        )
