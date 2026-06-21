// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

The balance ledger tracks the running balances for PO lines,
recording what's been delivered, invoiced, and what's remaining.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class BalanceLedger(Base):
    """Balance ledger entry model.

    Tracks running balances for PO lines including:
    - Total ordered
    - Total delivered
    - Total invoiced
    - Remaining to deliver
    - Remaining to invoice
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            name="uq_balance_ledger_po_line",
        ),
        Index("ix_balance_ledger_po_id", "po_id"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )

    # References to PO
    po_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Quantity balances
    ordered_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )
    delivered_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )
    approved_invoiced_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )

    # Amount balances
    ordered_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    delivered_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    approved_invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Last transaction tracking
    last_delivery_id: Mapped[UUID | None] = mapped_column(nullable=True)
    last_delivery_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_invoice_id: Mapped[UUID | None] = mapped_column(nullable=True)
    last_invoice_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )

    @property
    def remaining_to_deliver(self) -> Decimal:
        """Calculate remaining quantity to deliver."""
        return self.ordered_qty - self.delivered_qty

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.delivered_qty - self.invoiced_qty

    @property
    def pending_approval_qty(self) -> Decimal:
        """Calculate quantity pending approval."""
        return self.invoiced_qty - self.approved_invoiced_qty

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger PO:{self.po_id} Line:{self.po_line_id} "
            f"Ordered:{self.ordered_qty} Delivered:{self.delivered_qty} "
            f"Invoiced:{self.invoiced_qty}>"
        )


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
