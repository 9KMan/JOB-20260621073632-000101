# models/balance_ledger.py
"""Balance Ledger SQLAlchemy model for tracking PO/DN/Invoice balances."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Balance Ledger model.
    
    Tracks running balances for PO lines across invoices and delivery notes.
    This is the source of truth for what remains to be invoiced against a PO.
    """
    
    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )
    
    # References
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Transaction Details
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Quantities
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    
    # Amounts
    amount_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_change: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Metadata
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Processed By
    processed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger_entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger_entries",
    )
