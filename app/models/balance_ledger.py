// app/models/balance_ledger.py
"""Balance Ledger SQLAlchemy model for tracking PO line balances."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance Ledger model for tracking remaining balances on PO lines.
    
    This table maintains running balances for:
    - Ordered vs Delivered quantities
    - Ordered vs Invoiced quantities
    - Balance amounts
    """

    __tablename__ = "balance_ledger"

    # Reference to PO line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Product reference for learning
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Quantities
    original_ordered_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    delivered_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))
    invoiced_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))
    paid_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))

    # Amounts
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    delivered_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    invoiced_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))

    # Calculated balances
    balance_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Delivery balance
    delivery_balance_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    delivery_balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Invoice balance
    invoice_balance_qty: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    invoice_balance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Status
    is_fully_delivered: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_fully_invoiced: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_fully_paid: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Dates
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    po_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Last transaction tracking
    last_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    last_invoice_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_delivery_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    last_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint("po_line_id", name="uq_balance_ledger_po_line"),
        Index("ix_balance_vendor_product", "vendor_id", "product_code"),
        Index("ix_balance_po_id", "po_id"),
        Index("ix_balance_delivery_bal", "delivery_balance_qty"),
        Index("ix_balance_invoice_bal", "invoice_balance_amount"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, po_line={self.po_line_id}, balance={self.balance_amount})>"

    def recalculate_balances(self) -> None:
        """Recalculate all balance fields."""
        self.balance_qty = self.original_ordered_qty - self.invoiced_qty
        self.balance_amount = self.original_amount - self.invoiced_amount
        self.delivery_balance_qty = self.original_ordered_qty - self.delivered_qty
        self.delivery_balance_amount = self.original_amount - self.delivered_amount
        self.invoice_balance_qty = self.delivered_qty - self.invoiced_qty
        self.invoice_balance_amount = self.delivered_amount - self.invoiced_amount
        
        self.is_fully_delivered = self.delivered_qty >= self.original_ordered_qty
        self.is_fully_invoiced = self.invoiced_qty >= self.original_ordered_qty
        self.is_fully_paid = self.paid_qty >= self.original_ordered_qty


# Import for relationship resolution
from app.models.purchase_order import PurchaseOrder, POLine
