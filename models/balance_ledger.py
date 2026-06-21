# models/balance_ledger.py
"""Balance Ledger SQLAlchemy model.

Tracks the running balance for each PO line, including invoices, deliveries,
and payments. Provides audit trail for AP reconciliation.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import BalanceTransactionType

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import POLine, PurchaseOrder


class BalanceLedger(Base):
    """Balance Ledger model.

    Records all transactions affecting the balance for each PO line.
    Includes invoices, deliveries, credit notes, payments, and adjustments.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "po_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
        Index("ix_balance_ledger_created_at", "created_at"),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    transaction_type: Mapped[BalanceTransactionType] = mapped_column(
        String(30),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    running_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    running_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    po_line: Mapped["POLine"] = relationship(
        "POLine",
        back_populates="balance_ledger_entries",
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.transaction_type}: {self.amount}>"
