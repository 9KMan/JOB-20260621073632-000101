# models/balance_ledger.py
"""Balance Ledger SQLAlchemy model.

Tracks the open balances for PO lines and invoice lines.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Balance Ledger model.

    Tracks the open/paid balance for each PO line and invoice line.
    This is the source of truth for AP balance reporting.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_document_type", "document_type"),
        Index("ix_balance_ledger_document_number", "document_number"),
        Index("ix_balance_ledger_vendor_number", "vendor_number"),
        Index("ix_balance_ledger_due_date", "due_date"),
        Index("ix_balance_ledger_status", "status"),
        {"schema": None},
    )

    # Document references
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    document_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    # Parent references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Vendor info
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Financial amounts
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    open_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Quantity tracking
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    open_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    paid_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Dates
    document_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        index=True,
    )

    # Payment tracking
    paid_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    payment_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
        lazy="selectin",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}:{self.document_number}>"

    @property
    def is_fully_paid(self) -> bool:
        """Check if balance is fully paid."""
        return self.open_amount <= 0

    @property
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        if self.due_date is None or self.status != "open":
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self) -> int | None:
        """Calculate days overdue."""
        if not self.is_overdue or self.due_date is None:
            return None
        return (date.today() - self.due_date).days
