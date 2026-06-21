// models/balance_ledger.py
"""Balance ledger model definition for tracking PO balances."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Date,
    Numeric,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
    from models.invoice import Invoice


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger for tracking purchase order balances.
    
    Tracks the relationship between POs, invoices, and remaining balances.
    
    Attributes:
        id: UUID primary key
        po_id: Purchase order reference
        po_line_id: Optional PO line item reference
        invoice_id: Invoice reference
        transaction_type: Type of transaction (invoice, credit, adjustment)
        amount: Transaction amount
        running_balance: Remaining balance after this transaction
        transaction_date: Date of transaction
        notes: Transaction notes
    """
    
    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "po_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
    )
    
    po_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36),
        ForeignKey("purchase_order_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    running_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    po_line_item: Mapped["PurchaseOrderLineItem | None"] = relationship(
        "PurchaseOrderLineItem",
        back_populates="balance_ledger_entries",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )
