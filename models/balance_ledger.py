# models/balance_ledger.py
"""
BalanceLedger SQLAlchemy model.

Tracks running balances for PO lines to prevent over-invoicing.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance Ledger model for tracking PO line balances.
    
    Maintains a running balance for each PO line to track:
    - Ordered quantity/amount
    - Invoiced quantity/amount
    - Paid quantity/amount
    - Remaining balance
    
    This prevents over-invoicing and provides audit trail.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_entry_type", "entry_type"),
        {"schema": None},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Foreign Keys
    # ─────────────────────────────────────────────────────────────────────────
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        doc="PO line this balance entry belongs to",
    )
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Invoice line that caused this entry",
    )
    dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="DN line related to this entry",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Entry Type
    # ─────────────────────────────────────────────────────────────────────────
    entry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of ledger entry (order, invoice, payment, credit, adjustment)",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Quantities
    # ─────────────────────────────────────────────────────────────────────────
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity before this entry",
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity change (positive or negative)",
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity after this entry",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Amounts
    # ─────────────────────────────────────────────────────────────────────────
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Amount before this entry",
    )
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Amount change (positive or negative)",
    )
    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Amount after this entry",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────────────────
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Reference number (invoice number, payment ID, etc.)",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Description of this entry",
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created this entry",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.entry_type}: {self.quantity_change}>"


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrderLine
from models.invoice import InvoiceLine
from models.delivery_note import DeliveryNoteLine

# Add relationship back to PurchaseOrderLine
PurchaseOrderLine.balance_entries = relationship(
    "BalanceLedger",
    back_populates="po_line",
    cascade="all, delete-orphan",
    lazy="selectin",
)
