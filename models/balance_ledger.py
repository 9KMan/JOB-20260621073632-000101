# models/balance_ledger.py
"""Balance Ledger model definition."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import MatchStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger for tracking open balances per PO line."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_bl_po_line_id", "purchase_order_line_id"),
        Index("ix_bl_transaction_date", "transaction_date"),
        Index("ix_bl_reference_type", "reference_type"),
    )

    # Reference to PO Line
    purchase_order_line_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Transaction reference
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'invoice', 'dn', 'adjustment'
    reference_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False)

    # Transaction details
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'debit', 'credit'
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0"))
    amount_change: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # Running balance (calculated)
    running_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    running_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Match status for this balance entry
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Notes
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    purchase_order_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.reference_type}:{self.reference_number} - Qty: {self.running_quantity}>"

    def is_balanced(self) -> bool:
        """Check if the balance is zero (fully matched)."""
        return self.running_quantity == Decimal("0") and self.running_amount == Decimal("0")

    def get_open_quantity(self) -> Decimal:
        """Get the open quantity for this balance entry."""
        return self.running_quantity

    def get_open_amount(self) -> Decimal:
        """Get the open amount for this balance entry."""
        return self.running_amount
