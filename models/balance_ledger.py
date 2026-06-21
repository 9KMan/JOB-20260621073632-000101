# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking balances."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import LineStatus


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model for tracking PO/DN/Invoice balances."""

    __tablename__ = "balance_ledger"

    # Document References
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Purchase Order",
    )
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to PO Line",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Delivery Note",
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to DN Line",
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Invoice",
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Invoice Line",
    )

    # Balance Details
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Type: PO_BALANCE, DN_BALANCE, INVOICE_BALANCE",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Product code",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Balance quantity",
    )
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Original quantity",
    )

    # Amounts
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Balance amount",
    )
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Original amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
        doc="Balance status",
    )

    # Transaction Reference
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Transaction type: PO_CREATED, PO_RECEIVED, INVOICE_MATCHED, etc.",
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="Transaction reference ID",
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Transaction date",
    )

    # Relationships
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger_entries",
    )
    delivery_note_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="balance_ledger_entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger_entries",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line", "purchase_order_line_id"),
        Index("ix_balance_ledger_dn_line", "delivery_note_line_id"),
        Index("ix_balance_ledger_invoice_line", "invoice_line_id"),
        Index("ix_balance_ledger_type_status", "balance_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.balance_type} - Qty: {self.quantity}>"

    @property
    def is_settled(self) -> bool:
        """Check if balance is fully settled."""
        return self.quantity == Decimal("0") or self.amount == Decimal("0")
