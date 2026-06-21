// models/balance_ledger.py
"""BalanceLedger database model.

Tracks balance information for PO lines, enabling
calculation of remaining quantities and amounts.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, TimestampMixin):
    """Balance ledger entry model.

    Maintains running balances for PO lines to track:
    - Total ordered quantity
    - Delivered quantity
    - Invoiced quantity
    - Remaining balances
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        UniqueConstraint(
            "po_line_id",
            "invoice_line_id",
            name="uq_ledger_po_invoice_line",
        ),
        {"schema": "public"},
    )

    # Foreign keys
    po_line_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public.purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public.invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Balance quantities
    ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Balance amounts
    ordered_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
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

    # Unit price (for calculation)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    # Remaining balances (computed but stored for efficiency)
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # References
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_note_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps for audit
    last_invoice_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_delivery_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledgers",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger",
        uselist=False,
    )

    def update_balances(
        self,
        delivered_qty: Decimal | None = None,
        invoiced_qty: Decimal | None = None,
    ) -> None:
        """Update remaining balances after delivery or invoice.

        Args:
            delivered_qty: Quantity delivered in this transaction.
            invoiced_qty: Quantity invoiced in this transaction.
        """
        if delivered_qty is not None:
            self.delivered_quantity += delivered_qty
            self.delivered_amount += delivered_qty * self.unit_price

        if invoiced_qty is not None:
            self.invoiced_quantity += invoiced_qty
            self.invoiced_amount += invoiced_qty * self.unit_price

        self.remaining_quantity = self.ordered_quantity - self.delivered_quantity
        self.remaining_amount = self.ordered_amount - self.delivered_amount

    def __repr__(self) -> str:
        return f"<BalanceLedger po_line={self.po_line_id}>"
