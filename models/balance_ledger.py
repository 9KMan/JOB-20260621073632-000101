"""Balance ledger: per-PO-line running balance of received / invoiced quantities and value.

The ledger is the authoritative state used during matching: an invoice line can
only be approved if the cumulative invoiced value (after the current line is
applied) does not exceed the PO line's open balance within tolerance.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LedgerEventType(StrEnum):
    """Reason a ledger entry was created."""

    OPENING_BALANCE = "opening_balance"
    GOODS_RECEIVED = "goods_received"
    INVOICE_POSTED = "invoice_posted"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"


class BalanceLedger(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Current open balance snapshot for a single purchase order line."""

    __tablename__ = "balance_ledger"

    purchase_order_line_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    ordered_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    received_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    invoiced_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    open_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    ordered_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    invoiced_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    open_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")


class BalanceLedgerEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable, append-only event log; every balance change produces one row."""

    __tablename__ = "balance_ledger_entries"

    balance_ledger_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("balance_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_order_line_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[LedgerEventType] = mapped_column(String(32), nullable=False)
    delta_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    delta_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    reference_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index(
            "ix_balance_ledger_entries_po_line_event_time",
            "purchase_order_line_id",
            "created_at",
        ),
    )
