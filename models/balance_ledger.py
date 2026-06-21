// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances.

The balance ledger tracks the relationship between:
- Purchase Order lines (what was ordered)
- Delivery lines (what was delivered)
- Invoice lines (what was invoiced)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class BalanceLedger(Base):
    """Balance Ledger model for tracking PO line balances.

    Tracks the remaining quantities and amounts for each PO line
    after accounting for deliveries and invoices.

    Attributes:
        id: UUID primary key
        po_line_id: Reference to purchase order line
        delivery_note_line_id: Optional reference to delivery note line
        invoice_line_id: Optional reference to invoice line
        transaction_type: Type of transaction (delivery, invoice, adjustment)
        quantity_before: Quantity before this transaction
        quantity_change: Quantity changed by this transaction
        quantity_after: Quantity remaining
        amount_before: Amount before this transaction
        amount_change: Amount changed by this transaction
        amount_after: Amount remaining
    """

    __tablename__ = "balance_ledger"

    # References
    po_line_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_line_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Quantity tracking
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Amount tracking
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
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
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Running balance
    quantity_remaining: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    amount_remaining: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Reference document info
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    reference_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    is_reconciled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Additional data
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        backref="balance_entries",
    )

    __table_args__ = (
        Index("ix_balance_po_line", "po_line_id", "transaction_type"),
        Index("ix_balance_delivery", "delivery_note_line_id"),
        Index("ix_balance_invoice", "invoice_line_id"),
        Index("ix_balance_reference", "reference_number", "transaction_type"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger PO:{self.po_line_id} {self.transaction_type}>"

    @property
    def is_balanced(self) -> bool:
        """Check if the line is fully balanced (no remaining)."""
        return self.quantity_remaining == Decimal("0") and self.amount_remaining == Decimal("0")

    @property
    def balance_percentage(self) -> Decimal:
        """Calculate balance percentage."""
        original = self.quantity_before
        if original == Decimal("0"):
            return Decimal("0")
        return (self.quantity_remaining / original) * Decimal("100")
