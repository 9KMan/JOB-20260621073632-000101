# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO balances."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CommonMixin
from models.enums import MatchDecision


class BalanceLedger(Base, CommonMixin):
    """Balance Ledger model for tracking PO-to-invoice matching balances.

    This table maintains a running balance of what's been invoiced against
    each PO line, enabling partial matches and balance tracking.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "invoice_line_id",
            name="uq_balance_po_invoice_line",
        ),
        Index("ix_balance_po_line_id", "po_line_id"),
        Index("ix_balance_invoice_id", "invoice_id"),
        Index("ix_balance_po_id", "po_id"),
        Index("ix_balance_posting_date", "posting_date"),
        {"schema": None},
    )

    # Reference to Purchase Order
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_line_number: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Reference to Invoice
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Reference to Delivery Note (optional)
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Financial amounts
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Original PO line amount",
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Invoiced amount",
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Amount variance (invoice - po)",
    )

    # Quantities
    po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    invoice_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    # Match details
    match_decision: Mapped[MatchDecision] = mapped_column(
        nullable=False,
    )
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    match_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Cross reference ID from learning system",
    )

    # Balance tracking
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    closing_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Dates
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    posting_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Variances
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger PO:{self.po_number} INV:{self.invoice_number} "
            f"Amt:{self.invoice_amount}>"
        )

    @property
    def variance_percentage(self) -> float:
        """Calculate variance as percentage."""
        if self.po_amount == 0:
            return 0.0
        return float(self.variance_amount / self.po_amount * 100)

    @property
    def is_balanced(self) -> bool:
        """Check if entry is balanced (no variance)."""
        return self.variance_amount == Decimal("0.00")
