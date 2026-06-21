# models/balance_ledger.py
"""Balance ledger for tracking PO line balances."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance ledger for tracking quantities and amounts
    against Purchase Order lines.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )

    # Reference to PO line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Transaction reference
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # delivery, invoice, credit_memo, adjustment
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # DN number or Invoice number

    # Quantities
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Amounts
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="quantity",
    )  # quantity, amount, both

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    po_line = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )


class BalanceSummary(Base, UUIDMixin, TimestampMixin):
    """
    Denormalized balance summary per PO line.
    Updated on each transaction for fast lookups.
    """

    __tablename__ = "balance_summary"
    __table_args__ = (
        Index("ix_balance_summary_po_line_id", "po_line_id", unique=True),
    )

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_credited: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_credited: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Percentages
    delivery_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    invoice_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )


# Add relationships to PurchaseOrderLine
from models.purchase_order import PurchaseOrderLine

PurchaseOrderLine.balance_entries = relationship(
    "BalanceLedger",
    back_populates="po_line",
    cascade="all, delete-orphan",
    lazy="selectin",
)
