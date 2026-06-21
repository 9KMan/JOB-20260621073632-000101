# models/balance_ledger.py
"""Balance ledger model for tracking PO-to-invoice balances."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance ledger for tracking purchase order line balances.
    
    This table maintains a running balance for each PO line showing:
    - Total ordered quantity
    - Total invoiced quantity
    - Total delivered quantity
    - Remaining balance
    """

    __tablename__ = "balance_ledger"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    purchase_order_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_matched: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    
    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    amount_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    amount_matched: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    
    # Balance Status
    balance_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    
    # Metadata
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'invoice', 'delivery', 'adjustment'
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger"
    )
    purchase_order_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balance_ledger"
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line", "purchase_order_line_id"),
        Index("ix_balance_ledger_invoice", "invoice_id"),
        Index("ix_balance_ledger_po", "purchase_order_id", "transaction_type"),
    )

    @property
    def is_balanced(self) -> bool:
        """Check if the line is fully balanced."""
        return self.balance_quantity == Decimal("0") and self.balance_amount == Decimal("0")

    @property
    def balance_percentage(self) -> float:
        """Calculate balance percentage of the original order."""
        if self.quantity_ordered == Decimal("0"):
            return 0.0
        matched_ratio = self.quantity_matched / self.quantity_ordered
        return float(matched_ratio * 100)


from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.invoice import Invoice, InvoiceLine
