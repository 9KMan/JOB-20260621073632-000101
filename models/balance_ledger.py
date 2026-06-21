# models/balance_ledger.py
"""BalanceLedger and BalanceLedgerEntry SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Balance Ledger - tracks open balances per PO line.
    
    This is the source of truth for how much is left to invoice
    against each PO line. Created when a PO is ingested.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id", unique=True),
        Index("ix_balance_ledger_vendor_number", "vendor_number"),
        Index("ix_balance_ledger_status", "status"),
        UniqueConstraint("po_line_id", name="uq_balance_ledger_po_line_id"),
    )

    # Foreign key to PO line
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Reference info
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="PO number for quick reference",
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Vendor number",
    )

    # Balance amounts
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Original ordered quantity",
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Total delivered quantity",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Total invoiced quantity",
    )
    quantity_remaining: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Remaining quantity to invoice",
    )

    # Financial balances
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Original line amount",
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total invoiced amount",
    )
    amount_remaining: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Remaining amount to invoice",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        comment="Balance status: open, closed, over_invoiced",
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )
    entries: Mapped[list["BalanceLedgerEntry"]] = relationship(
        "BalanceLedgerEntry",
        back_populates="balance_ledger",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if balance is fully invoiced."""
        return self.quantity_remaining <= 0

    @property
    def over_invoice_amount(self) -> Decimal:
        """Calculate over-invoice amount if any."""
        if self.amount_remaining < 0:
            return abs(self.amount_remaining)
        return Decimal("0.00")

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, po_number={self.po_number}, remaining={self.quantity_remaining})>"


class BalanceLedgerEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual ledger entry tracking invoice-to-PO balance changes.
    
    Each entry represents a debit (invoice) or credit (reversal)
    against the balance ledger.
    """

    __tablename__ = "balance_ledger_entries"
    __table_args__ = (
        Index("ix_balance_ledger_entries_ledger_id", "ledger_id"),
        Index("ix_balance_ledger_entries_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_entries_entry_date", "entry_date"),
        Index("ix_balance_ledger_entries_entry_type", "entry_type"),
        UniqueConstraint(
            "ledger_id", "invoice_line_id", "entry_type",
            name="uq_balance_ledger_entries_ledger_invoice_type"
        ),
    )

    # Foreign keys
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledger.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entry tracking
    entry_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Entry type: debit, credit",
    )
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of the entry",
    )
    entry_sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequence number for ordering entries",
    )

    # Invoice reference
    invoice_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Invoice number",
    )
    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Invoice date",
    )

    # Quantities
    quantity_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Quantity change (positive for debit, negative for credit)",
    )
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Balance quantity before this entry",
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Balance quantity after this entry",
    )

    # Amounts
    amount_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Amount change (positive for debit, negative for credit)",
    )
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Balance amount before this entry",
    )
    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Balance amount after this entry",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Entry notes or reason",
    )

    # Relationships
    balance_ledger: Mapped["BalanceLedger"] = relationship(
        "BalanceLedger",
        back_populates="entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_entries",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedgerEntry(id={self.id}, type={self.entry_type}, delta={self.quantity_delta})>"
