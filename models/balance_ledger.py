# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance ledger tracking for PO lines."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint("po_line_id", name="uq_balance_ledger_po_line"),
        Index("ix_balance_ledger_po_id", "po_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    quantity_to_receive: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_to_invoice: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_received: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_to_receive: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_to_invoice: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Last activity tracking
    last_receipt_date: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    last_invoice_date: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger po_line={self.po_line_id} to_receive={self.quantity_to_receive}>"

    @property
    def quantity_variance(self) -> Decimal:
        """Calculate quantity variance (received - invoiced)."""
        return self.quantity_received - self.quantity_invoiced

    @property
    def amount_variance(self) -> Decimal:
        """Calculate amount variance (received - invoiced)."""
        return self.amount_received - self.amount_invoiced

    @property
    def is_fully_received(self) -> bool:
        """Check if all ordered quantity has been received."""
        return self.quantity_to_receive == Decimal("0.00")

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if all received quantity has been invoiced."""
        return self.quantity_to_invoice == Decimal("0.00")

    @property
    def is_balanced(self) -> bool:
        """Check if the ledger is balanced."""
        return (
            self.quantity_received == self.quantity_invoiced
            and self.amount_received == self.amount_invoiced
        )
