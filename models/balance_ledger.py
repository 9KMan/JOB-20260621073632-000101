// models/balance_ledger.py
"""Balance Ledger SQLAlchemy model."""

from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import LineStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance Ledger for tracking PO line balances.

    This table maintains the running balance for each PO line,
    tracking quantities and amounts across receipts and invoices.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
        Index("ix_balance_ledger_created_at", "created_at"),
        {
            "schema": "public",
        },
    )

    # PO Line reference
    po_line_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        doc="PO line this balance belongs to",
    )

    # Transaction reference
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Type: RECEIPT, INVOICE, CREDIT_MEMO, ADJUSTMENT",
    )
    transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Reference to source document (DN, Invoice, etc.)",
    )
    transaction_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        doc="Reference to source line",
    )

    # Date information
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date of transaction",
    )
    posting_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date to post to ledger",
    )

    # Quantities
    opening_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Quantity before this transaction",
    )
    transaction_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Quantity added/deducted by this transaction",
    )
    closing_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Quantity after this transaction",
    )

    # Amounts
    opening_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Amount before this transaction",
    )
    transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Amount added/deducted by this transaction",
    )
    closing_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Amount after this transaction",
    )

    # Unit price for calculations
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price at time of transaction",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        doc="Entry status",
    )

    # User tracking
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created the entry",
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved the entry",
    )

    # Additional metadata
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Notes or reference",
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger(id={self.id}, po_line_id={self.po_line_id}, "
            f"type={self.transaction_type}, qty={self.transaction_quantity})>"
        )
