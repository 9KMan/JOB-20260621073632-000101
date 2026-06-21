# models/balance_ledger.py
"""Balance Ledger model for tracking invoice-to-PO balances."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import POLine


class BalanceLedger(TimestampMixin, UUIDMixin, Base):
    """
    Balance Ledger tracks the running balance between invoices and PO lines.
    
    Each record represents a transactional entry showing how much of a PO line
    has been invoiced, delivered, and the remaining balance.
    """
    
    __tablename__ = "balance_ledger"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Quantities
    po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        description="Original PO line quantity",
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        description="Quantity delivered via delivery notes",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        description="Quantity on this invoice",
    )
    previous_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        description="Previously invoiced quantity against this PO line",
    )
    
    # Amounts
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        description="Original PO line net amount",
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        description="Invoice line net amount",
    )
    previous_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
        description="Previously invoiced amount",
    )
    
    # Balance calculation
    quantity_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        description="Remaining quantity balance (delivered - invoiced)",
    )
    amount_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        description="Remaining amount balance",
    )
    
    # Status
    balance_status: Mapped[str] = mapped_column(
        String(20),
        default="balanced",
        nullable=False,
        description="Balance status: balanced, over, under",
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )
    po_line: Mapped["POLine"] = relationship(
        "POLine",
        back_populates="balance_ledger_entries",
    )
    
    __table_args__ = (
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_status", "balance_status"),
        Index("ix_balance_ledger_invoice_po", "invoice_id", "po_line_id", unique=True),
    )
