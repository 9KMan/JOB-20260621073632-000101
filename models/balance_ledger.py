# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

Tracks balances and history for PO lines across invoices and deliveries.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger model for tracking PO line balances.

    Maintains running balances for:
    - Quantity ordered vs delivered
    - Quantity delivered vs invoiced
    - Amount invoiced vs paid

    Attributes:
        transaction_type: Type of transaction (invoice, delivery, payment)
        quantity_change: Change in quantity
        amount_change: Change in amount
        running_quantity: Current running quantity balance
        running_amount: Current running amount balance
    """

    __tablename__ = "balance_ledger"

    # Transaction references
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    transaction_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # PO reference (main anchor)
    purchase_order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Invoice reference
    invoice_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Financial quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_paid: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    amount_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    amount_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    # Balance snapshots
    balance_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    # Metadata
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    effective_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates=None,
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_date", "purchase_order_id", "effective_date"),
        Index("ix_balance_ledger_invoice", "invoice_id"),
        Index("ix_balance_ledger_ref", "reference_number"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.transaction_type}: {self.balance_quantity} qty, {self.balance_amount} amount>"
