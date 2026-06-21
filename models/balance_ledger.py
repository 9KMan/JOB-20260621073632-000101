# models/balance_ledger.py
"""Balance Ledger SQLAlchemy model for tracking open balances."""

import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance ledger for tracking PO line balances."""

    __tablename__ = "balance_ledger"

    # Reference to PO Line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reference to PO Header
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vendor
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Balances
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )

    # Calculated balances
    open_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    open_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Financial
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Dates
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    po_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
        index=True,
    )

    # Last activity
    last_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
    )

    __table_args__ = (
        Index("ix_balance_ledger_vendor_status", "vendor_id", "status"),
        Index("ix_balance_ledger_open", "status", "open_amount"),
    )
