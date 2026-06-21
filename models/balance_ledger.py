// models/balance_ledger.py
"""Balance Ledger model definition.

This module defines the BalanceLedger SQLAlchemy model representing
the running balance between POs, DNs, and Invoices.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class BalanceLedger(Base):
    """Balance Ledger model.

    Tracks the running balance for PO lines, including:
    - Ordered quantity
    - Received quantity (from DNs)
    - Invoiced quantity/amount
    - Paid quantity/amount
    - Outstanding balance

    This is the foundation for the matching engine's balance tracking.

    Attributes:
        id: UUID primary key
        po_id: Reference to purchase order
        po_line_id: Reference to specific PO line
        invoice_id: Reference to matched invoice (if any)
        line_amount: Original PO line amount
        ordered_qty: Original ordered quantity
        received_qty: Total received quantity (from DNs)
        invoiced_qty: Total invoiced quantity
        invoiced_amount: Total invoiced amount
        paid_qty: Total paid quantity
        paid_amount: Total paid amount
        open_qty: Remaining open quantity
        open_amount: Remaining open amount
        currency: Currency code
        last_activity_at: Last balance change timestamp
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "balance_ledger"

    # References
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to purchase order",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to PO line",
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched invoice",
    )

    # Item tracking
    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Item code being tracked",
    )

    # Quantities
    ordered_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        doc="Original ordered quantity",
    )
    received_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        doc="Total received quantity",
    )
    invoiced_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        doc="Total invoiced quantity",
    )
    paid_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        doc="Total paid quantity",
    )

    # Amounts
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
        doc="Original line amount",
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
        doc="Total invoiced amount",
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
        doc="Total paid amount",
    )

    # Calculated balances
    open_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        doc="Remaining open quantity",
    )
    open_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
        doc="Remaining open amount",
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code",
    )

    # Last activity
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last balance change timestamp",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )

    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "purchase_order_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_item_code", "item_code"),
        Index("ix_balance_ledger_open_amount", "open_amount"),
    )

    def __repr__(self) -> str:
        """String representation of BalanceLedger."""
        return f"<BalanceLedger(id={self.id}, item={self.item_code}, open_amount={self.open_amount})>"

    def calculate_open_balance(self) -> None:
        """Calculate open quantity and amount based on current values."""
        self.open_qty = self.ordered_qty - self.invoiced_qty
        self.open_amount = self.line_amount - self.invoiced_amount
        self.last_activity_at = datetime.now(timezone.utc)

    def add_invoice_allocation(
        self,
        qty: Decimal,
        amount: Decimal,
        invoice_id: uuid.UUID,
    ) -> None:
        """Add invoice allocation to the balance.

        Args:
            qty: Invoiced quantity to add
            amount: Invoiced amount to add
            invoice_id: Reference to the invoice
        """
        self.invoiced_qty += qty
        self.invoiced_amount += amount
        self.invoice_id = invoice_id
        self.calculate_open_balance()

    def add_payment(
        self,
        qty: Decimal,
        amount: Decimal,
    ) -> None:
        """Record payment against the balance.

        Args:
            qty: Paid quantity
            amount: Paid amount
        """
        self.paid_qty += qty
        self.paid_amount += amount
        self.calculate_open_balance()


# Import uuid
import uuid
