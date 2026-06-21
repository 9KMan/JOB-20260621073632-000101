# models/balance_ledger.py
"""
BalanceLedger SQLAlchemy models.

Tracks running balances for PO lines to support invoice
matching and prevent over-invoicing.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import LedgerEntryType

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class BalanceLedger(Base):
    """
    Balance Ledger model.
    
    Tracks the running balance for each PO line to prevent
    over-invoicing and support invoice matching decisions.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_entry_type", "entry_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
        UniqueConstraint(
            "po_line_id", "entry_type", "reference_id",
            name="uq_balance_entry_unique"
        ),
        {"schema": None},
    )

    # References
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Entry details
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        SQLEnum(LedgerEntryType, name="ledger_entry_type", create_type=True),
        nullable=False,
        index=True,
        comment="Type of ledger entry",
    )

    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Reference to the source document",
    )

    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable reference number",
    )

    # Amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity for this entry",
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Monetary amount for this entry",
    )

    # Balance tracking
    running_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Running quantity balance after this entry",
    )

    running_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Running monetary balance after this entry",
    )

    # Balance limits
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Original PO quantity",
    )

    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Original PO amount",
    )

    # Flags
    is_over_limit: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Whether entry causes over-limit",
    )

    over_limit_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity over the limit",
    )

    over_limit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Amount over the limit",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Entry notes",
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional metadata as JSON",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="balance_entries",
    )

    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )

    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.entry_type}: {self.reference_number} = {self.amount}>"

    @property
    def available_quantity(self) -> Decimal:
        """Calculate available quantity."""
        return self.original_quantity - self.running_quantity

    @property
    def available_amount(self) -> Decimal:
        """Calculate available amount."""
        return self.original_amount - self.running_amount

    @property
    def utilization_percentage(self) -> float:
        """Calculate balance utilization percentage."""
        if self.original_amount == 0:
            return 0.0
        return float((self.running_amount / self.original_amount) * 100)
