# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO balances."""

from datetime import datetime, timezone
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

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance ledger for tracking PO line balances after invoice matching."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "purchase_order_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_po_line_id", "purchase_order_line_id"),
        UniqueConstraint(
            "purchase_order_line_id",
            "invoice_id",
            name="uq_balance_ledger_po_line_invoice",
        ),
        {"schema": "public"},
    )

    purchase_order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("public.purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("public.purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("public.invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    original_po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    original_po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    match_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    match_type: Mapped[str] = mapped_column(
        String(50),
        default="direct",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates=None,
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_ledger",
    )
