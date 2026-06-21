# models/balance_ledger.py
"""Balance Ledger model for AP Automation Core Engine."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Index,
    Numeric,
    String,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLineItem
    from models.invoice import InvoiceLineItem


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance Ledger model tracking open balances for PO lines.
    
    This model maintains the running balance of what has been delivered
    and invoiced against each purchase order line item.
    
    Attributes:
        id: UUID primary key
        po_line_item_id: Reference to the PO line item
        original_quantity: Original PO quantity
        quantity_delivered: Total quantity delivered via delivery notes
        quantity_invoiced: Total quantity invoiced
        quantity_credited: Total quantity credited
        quantity_open: Open quantity available for invoicing
        original_amount: Original PO line amount
        amount_delivered: Amount for delivered goods
        amount_invoiced: Amount invoiced
        amount_credited: Amount credited
        amount_open: Open amount available for invoicing
        last_delivery_date: Date of last delivery
        last_invoice_date: Date of last invoice
        status: Current balance status
    """

    __tablename__ = "balance_ledger"

    # References
    po_line_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_line_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Quantity tracking
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_credited: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_open: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    amount_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    amount_credited: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    amount_open: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Dates
    last_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
    )

    # Relationships
    po_line_item: Mapped["PurchaseOrderLineItem"] = relationship(
        "PurchaseOrderLineItem",
        back_populates="balance_ledgers",
    )
    invoice_line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        "InvoiceLineItem",
        back_populates="balance_ledger",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line_item_id", "po_line_item_id", unique=True),
        Index("ix_balance_ledger_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger PO Line {self.po_line_item_id} - Open: {self.quantity_open}>"

    def update_from_delivery(
        self,
        quantity: Decimal,
        delivery_date: date,
    ) -> None:
        """Update balance from a delivery note."""
        self.quantity_delivered += quantity
        self.amount_delivered = (
            self.quantity_delivered / self.original_quantity
        ) * self.original_amount if self.original_quantity else Decimal("0")
        self.last_delivery_date = delivery_date
        self._recalculate_open()

    def update_from_invoice(
        self,
        quantity: Decimal,
        amount: Decimal,
        invoice_date: date,
    ) -> None:
        """Update balance from an invoice."""
        self.quantity_invoiced += quantity
        self.amount_invoiced += amount
        self.last_invoice_date = invoice_date
        self._recalculate_open()

    def update_from_credit(
        self,
        quantity: Decimal,
        amount: Decimal,
    ) -> None:
        """Update balance from a credit memo."""
        self.quantity_credited += quantity
        self.amount_credited += amount
        self._recalculate_open()

    def _recalculate_open(self) -> None:
        """Recalculate open quantities and amounts."""
        self.quantity_open = (
            self.original_quantity
            - self.quantity_delivered
            - self.quantity_invoiced
            - self.quantity_credited
        )
        self.amount_open = (
            self.original_amount
            - self.amount_delivered
            - self.amount_invoiced
            - self.amount_credited
        )
        self.status = "closed" if self.quantity_open <= 0 else "open"
