# models/balance_ledger.py
"""Balance Ledger SQLAlchemy model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import POLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model for tracking PO line balances."""

    __tablename__ = "balance_ledger"

    po_line_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    transaction_date: Mapped[datetime] = mapped_column(
        nullable=False,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    po_line: Mapped["POLine"] = relationship(
        "POLine",
        back_populates="balance_ledger_entries",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
    )

    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "transaction_type",
            "reference",
            name="uq_balance_ledger_po_ref",
        ),
        Index("ix_balance_ledger_po_date", "po_line_id", "transaction_date"),
        Index("ix_balance_ledger_invoice", "invoice_id"),
    )
