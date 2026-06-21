# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

Tracks running balances for PO lines.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import BalanceType

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger for tracking PO line balances.

    Records all transactions affecting a PO line's balance:
    - Invoices applied
    - Credit notes
    - Payments
    - Adjustments

    The running balance can be calculated by summing all entries
    for a given PO line.
    """

    __tablename__ = "balance_ledger"

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reference_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reference_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    quantity_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    amount_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    running_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    running_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_date", "po_line_id", "transaction_date"),
        Index("ix_balance_ledger_reference", "reference_type", "reference_id"),
        UniqueConstraint(
            "reference_id",
            "transaction_type",
            name="uq_ledger_reference_transaction",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.reference_number} "
            f"qty_delta={self.quantity_delta} amt_delta={self.amount_delta}>"
        )

    @classmethod
    def create_invoice_entry(
        cls,
        po_line_id: uuid.UUID,
        invoice_id: uuid.UUID,
        invoice_number: str,
        quantity_delta: Decimal,
        amount_delta: Decimal,
        currency: str = "USD",
        notes: str | None = None,
    ) -> dict:
        """Create ledger entry data for an invoice.

        Args:
            po_line_id: PO line ID
            invoice_id: Invoice ID
            invoice_number: Invoice number
            quantity_delta: Quantity being invoiced (positive)
            amount_delta: Amount being invoiced (positive)
            currency: Currency code
            notes: Optional notes

        Returns:
            dict: Ledger entry data
        """
        return {
            "po_line_id": po_line_id,
            "transaction_type": BalanceType.INVOICE.value,
            "reference_type": "invoice",
            "reference_id": invoice_id,
            "reference_number": invoice_number,
            "quantity_delta": quantity_delta,
            "amount_delta": amount_delta,
            "currency": currency,
            "notes": notes,
        }

    @classmethod
    def create_credit_note_entry(
        cls,
        po_line_id: uuid.UUID,
        credit_note_id: uuid.UUID,
        credit_note_number: str,
        quantity_delta: Decimal,
        amount_delta: Decimal,
        currency: str = "USD",
        notes: str | None = None,
    ) -> dict:
        """Create ledger entry data for a credit note.

        Args:
            po_line_id: PO line ID
            credit_note_id: Credit note ID
            credit_note_number: Credit note number
            quantity_delta: Quantity being credited (negative)
            amount_delta: Amount being credited (negative)
            currency: Currency code
            notes: Optional notes

        Returns:
            dict: Ledger entry data
        """
        return {
            "po_line_id": po_line_id,
            "transaction_type": BalanceType.CREDIT_NOTE.value,
            "reference_type": "credit_note",
            "reference_id": credit_note_id,
            "reference_number": credit_note_number,
            "quantity_delta": quantity_delta,
            "amount_delta": amount_delta,
            "currency": currency,
            "notes": notes,
        }
