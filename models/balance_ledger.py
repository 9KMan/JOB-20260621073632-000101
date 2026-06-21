# models/balance_ledger.py
"""BalanceLedger and LedgerEntryType SQLAlchemy models.

Tracks the running balance of PO lines against invoices and delivery notes.
Used to determine what's remaining to invoice or receive.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import LedgerEntryType

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger for tracking PO line balances.

    Maintains a running balance for each PO line showing:
    - Total ordered
    - Total received (via delivery notes)
    - Total invoiced
    - Remaining to invoice/receive

    Attributes:
        entry_type: Type of ledger entry (invoice, delivery, adjustment)
        po_line_id: Reference to PO line
        invoice_line_id: Optional reference to invoice line
        quantity: Quantity for this entry
        amount: Monetary amount for this entry
        running_balance: Balance after this entry
        reference_id: External reference (invoice number, DN number, etc.)
        reference_date: Date of the reference document
        notes: Optional notes
    """

    __tablename__ = "balance_ledger"

    # Entry identification
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        Enum(LedgerEntryType, name="ledger_entry_type"),
        nullable=False,
        index=True,
    )

    # References
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_order_lines.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "invoice_lines.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
        index=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "delivery_note_lines.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )

    # Running balances (denormalized for performance)
    running_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    running_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Reference information
    reference_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    reference_date: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    entry_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger_entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger_entries",
    )

    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "entry_number",
            name="uq_ledger_po_line_entry",
        ),
        Index("ix_ledger_po_line_running", "po_line_id", "running_quantity"),
        Index("ix_ledger_reference", "reference_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.entry_type.value} - "
            f"Qty: {self.quantity} - Ref: {self.reference_id}>"
        )

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit entry (increases balance)."""
        return self.entry_type in (
            LedgerEntryType.INVOICE,
            LedgerEntryType.MANUAL_ADJUSTMENT,
        )

    @property
    def is_credit(self) -> bool:
        """Check if this is a credit entry (decreases balance)."""
        return self.entry_type in (
            LedgerEntryType.DELIVERY_NOTE,
            LedgerEntryType.CREDIT_NOTE,
        )
