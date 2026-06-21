# models/balance_ledger.py
"""Balance Ledger SQLAlchemy model.

Tracks running balances for PO lines to support matching calculations.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance Ledger database model.

    Tracks cumulative balances for each PO line across deliveries and invoices.
    This provides a real-time view of what's been delivered vs invoiced.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "transaction_type",
            "transaction_id",
            name="uq_ledger_transaction",
        ),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
        {"schema": None},
    )

    # References
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Document references
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Quantity balance
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )

    # Value balance
    value_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    value_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    value_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Metadata
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Transaction types
    TYPE_DELIVERY = "delivery"
    TYPE_INVOICE = "invoice"
    TYPE_CREDIT = "credit"
    TYPE_ADJUSTMENT = "adjustment"

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger po_line={self.po_line_id} "
            f"type={self.transaction_type} qty_delta={self.quantity_delta}>"
        )

    @property
    def is_delivery(self) -> bool:
        """Check if transaction is a delivery."""
        return self.transaction_type == self.TYPE_DELIVERY

    @property
    def is_invoice(self) -> bool:
        """Check if transaction is an invoice."""
        return self.transaction_type == self.TYPE_INVOICE

    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit."""
        return self.transaction_type == self.TYPE_CREDIT

    @property
    def is_adjustment(self) -> bool:
        """Check if transaction is an adjustment."""
        return self.transaction_type == self.TYPE_ADJUSTMENT
