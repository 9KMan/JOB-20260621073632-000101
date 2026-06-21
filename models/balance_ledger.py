# models/balance_ledger.py
"""BalanceLedger — balance tracking per PO line (I × P − D − B)."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Numeric,
    String,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine
    from models.invoice import InvoiceLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance ledger — tracks the running balance of a PO line as transactions
    (invoices and deliveries) are recorded.

    Balance formula per PO line:
        balance = ordered_qty
                - invoiced_qty
                - delivered_qty
                - written_off_qty

    A positive balance means there is still quantity available on the PO line.

    Attributes
    ----------
    transaction_type : str
        INVOICE | DELIVERY | WRITE_OFF | ADJUSTMENT
    quantity : Decimal
        Quantity change (positive or negative).
    amount : Decimal
        Financial amount associated with this transaction.
    reference : str | None
        External reference (e.g. invoice number, DN number).
    po_line_id : uuid.UUID
        The PO line this balance entry belongs to.
    invoice_line_id : uuid.UUID | None
        The invoice line that triggered this entry (if transaction_type == INVOICE).
    """

    __tablename__ = "balance_ledger"

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────

    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger_entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger_entries",
    )

    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "invoice_line_id",
            name="uq_balance_ledger_invoice_line",
        ),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
    )
