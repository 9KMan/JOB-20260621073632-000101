# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import BalanceType


class BalanceLedger(Base, TimestampMixin):
    """Balance ledger for tracking PO line quantities and amounts.

    Maintains a running balance of ordered, delivered, invoiced, and paid
    quantities/amounts for each PO line. Enables reconciliation and
    prevents over-delivery/invoicing.
    """

    __tablename__ = "balance_ledger"

    # Reference to PO line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reference to related documents
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(
        nullable=False,
        index=True,
    )

    # Quantities
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Amounts
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Reference
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Description
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_dn_id", "delivery_note_id"),
        Index("ix_balance_ledger_balance_type", "balance_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.balance_type.value} - "
            f"Qty: {self.quantity_change} ({self.quantity_before} -> {self.quantity_after})>"
        )
