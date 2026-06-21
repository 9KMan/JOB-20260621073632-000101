// models/balance_ledger.py
"""Balance Ledger model for tracking PO-to-Invoice balances."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CustomMixin
from models.enums import LineItemStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, CustomMixin):
    """Balance Ledger for tracking amounts against PO lines.

    This table maintains running balances of:
    - Ordered vs Invoiced amounts per PO line
    - Ordered vs Delivered amounts per PO line
    - Delivered vs Invoiced amounts

    Attributes:
        po_line_id: Reference to PO line.
        invoice_line_id: Reference to invoice line (optional).
        transaction_type: Type of transaction (PO, INV, DN, ADJ).
        transaction_id: ID of the transaction document.
        transaction_date: Date of the transaction.
        quantity: Quantity in this transaction.
        unit_price: Unit price.
        amount: Transaction amount (quantity * unit_price).
        running_balance_qty: Running balance of quantity.
        running_balance_amt: Running balance of amount.
        status: Current status of the balance record.
        description: Transaction description.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "transaction_type",
            "transaction_id",
            name="uq_balance_transaction",
        ),
        Index("ix_balance_po_line_id", "po_line_id"),
        Index("ix_balance_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_status", "status"),
        Index("ix_balance_created_at", "created_at"),
        {"schema": None},
    )

    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    transaction_date: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    running_balance_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    running_balance_amt: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=LineItemStatus.OPEN.value,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_records",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        foreign_keys=[invoice_line_id],
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.transaction_type} - {self.amount}>"
