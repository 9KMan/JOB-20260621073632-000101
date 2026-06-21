// models/balance_ledger.py
"""Balance Ledger model definition.

This module defines the BalanceLedger SQLAlchemy model for tracking
PO line balances after invoices and deliveries.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class BalanceLedger(Base):
    """Balance Ledger database model.

    Tracks running balances for PO lines across invoices and deliveries.
    This is the authoritative source for what's left to invoice.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_tenant_po_line", "tenant_id", "po_line_id"),
        Index("ix_balance_ledger_document", "document_type", "document_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # PO Line reference
    po_line_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Document reference
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_number: Mapped[str] = mapped_column(String(100), nullable=False)

    # Balance tracking
    # Positive = money owed to vendor, Negative = overpayment
    quantity_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )
    amount_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Original amounts
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Running totals
    total_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )
    total_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    po_line: Mapped["POLine"] = relationship("POLine")

    def __repr__(self) -> str:
        return f"<BalanceLedger PO Line {self.po_line_id}: Qty {self.quantity_balance}>"

    @property
    def can_invoice(self) -> bool:
        """Check if there is quantity available to invoice."""
        return self.quantity_balance > Decimal("0")

    @property
    def is_over_delivered(self) -> bool:
        """Check if more has been delivered than ordered."""
        return self.total_delivered > self.original_quantity

    @property
    def is_over_invoiced(self) -> bool:
        """Check if more has been invoiced than delivered."""
        return self.total_invoiced > self.total_delivered


# Import at bottom to avoid circular imports
from models.purchase_order import POLine
