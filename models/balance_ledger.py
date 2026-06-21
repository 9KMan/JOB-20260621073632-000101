// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDPrimaryKey, TimestampMixin):
    """Balance Ledger model for tracking PO line invoicing balances.

    This table provides an immutable audit trail of all invoice
    applications against purchase order lines.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_bl_po_line_id", "purchase_order_line_id"),
        Index("ix_bl_transaction_type", "transaction_type"),
        Index("ix_bl_posted_date", "posted_date"),
        UniqueConstraint(
            "purchase_order_line_id",
            "transaction_id",
            "transaction_type",
            name="uq_bl_po_line_transaction",
        ),
    )

    # Reference to PO Line
    purchase_order_line_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction Reference
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    transaction_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Balance Tracking
    posted_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Amounts
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    applied_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    balance_remaining: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Quantity Tracking
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    applied_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_remaining: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    purchase_order_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.transaction_type} "
            f"applied={self.applied_amount} "
            f"remaining={self.balance_remaining}>"
        )

    @classmethod
    def create_invoice_entry(
        cls,
        po_line_id: str,
        invoice_id: str,
        amount: Decimal,
        quantity: Decimal,
        original_balance: Decimal,
        original_qty: Decimal,
    ) -> "BalanceLedger":
        """Factory method to create an invoice ledger entry.

        Args:
            po_line_id: Purchase order line ID
            invoice_id: Invoice ID reference
            amount: Invoice amount applied
            quantity: Invoice quantity applied
            original_balance: Previous balance amount
            original_qty: Previous balance quantity

        Returns:
            New BalanceLedger instance
        """
        return cls(
            purchase_order_line_id=po_line_id,
            transaction_type="invoice",
            transaction_id=invoice_id,
            posted_date=date.today(),
            original_amount=original_balance,
            applied_amount=amount,
            balance_remaining=original_balance - amount,
            original_quantity=original_qty,
            applied_quantity=quantity,
            quantity_remaining=original_qty - quantity,
            status="active",
        )
