# models/balance_ledger.py
"""BalanceLedger and BalanceLedgerLine models — per-PO-line quantity/amount balances."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, Timestamps, UUIDPrimaryKey


class BalanceLedger(Base, UUIDPrimaryKey, Timestamps):
    """
    Balance ledger at the PO level.
    Mirrors the total open balance across all lines of one PO.
    """

    __tablename__ = "balance_ledgers"

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    currency: Mapped[str] = mapped_column(default="USD", nullable=False)
    total_open_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    po: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger",
    )
    lines: Mapped[list["BalanceLedgerLine"]] = relationship(
        "BalanceLedgerLine",
        back_populates="ledger",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("po_id", name="uq_balance_ledger_po_id"),
    )


class BalanceLedgerLine(Base, UUIDPrimaryKey, Timestamps):
    """
    Balance ledger at the PO-line level.
    One record per PO line, tracking open qty and amount.
    """

    __tablename__ = "balance_ledger_lines"

    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Quantities ──────────────────────────────────────────────────────────
    qty_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    qty_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
    )
    qty_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
    )
    qty_pending: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )  # remaining undelivered + uninvoiced

    # ── Amounts ──────────────────────────────────────────────────────────────
    amount_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    amount_pending: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    ledger: Mapped["BalanceLedger"] = relationship("BalanceLedger", back_populates="lines")
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_line",
    )

    __table_args__ = (
        UniqueConstraint("po_line_id", name="uq_balance_ledger_line_po_line_id"),
        Index("ix_balance_ledger_lines_po_line_id", "po_line_id"),
    )


# ── Forward reference resolution ──────────────────────────────────────────────
from models.purchase_order import PurchaseOrder, PurchaseOrderLine  # noqa: E402, F401
