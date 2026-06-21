// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

Tracks balances and quantities for PO lines across invoices and delivery notes.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model.

    Tracks quantities and amounts for each PO line across invoices and delivery notes.
    Used to calculate pending balances and detect over/under delivery.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "purchase_order_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        UniqueConstraint(
            "purchase_order_line_id",
            "invoice_id",
            "transaction_type",
            "reference_id",
            name="uq_balance_ledger_po_line_invoice_type_ref",
        ),
        {"schema": None},
    )

    # References
    purchase_order_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Transaction Details
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Amounts
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    # Timestamps
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    purchase_order_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.transaction_type} for PO Line {self.purchase_order_line_id}>"

    @property
    def is_active(self) -> bool:
        """Check if this ledger entry is active (not reversed)."""
        return self.status == "active" and self.reversed_at is None

    def reverse(self) -> None:
        """Reverse this ledger entry."""
        self.status = "reversed"
        self.reversed_at = datetime.now(timezone.utc)
