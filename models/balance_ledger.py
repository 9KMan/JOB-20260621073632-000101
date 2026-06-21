// models/balance_ledger.py
"""Balance Ledger SQLAlchemy model.

This module defines the BalanceLedger database model for tracking
remaining balances on purchase orders.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model for tracking PO balances.

    This table maintains a running balance of amounts remaining
    on purchase orders after invoices and payments are applied.

    Attributes:
        purchase_order_id: Associated PO
        invoice_id: Associated invoice (if applicable)
        po_line_id: Specific PO line (if line-level tracking)
        document_type: Type of document affecting balance
        document_number: Reference number of document
        debit_amount: Amount deducted from balance
        credit_amount: Amount added back to balance
        balance_after: Running balance after transaction
        transaction_date: Date of transaction
        description: Transaction description
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "purchase_order_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
    )

    # Foreign keys
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Document reference
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Amounts
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Dates
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Metadata
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledgers",
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_ledgers",
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.document_type}:{self.document_number} "
            f"({self.debit_amount} / {self.credit_amount})>"
        )
