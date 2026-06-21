# models/balance_ledger.py
"""BalanceLedger SQLAlchemy models.

Tracks running balances for PO lines based on deliveries and invoices.
"""

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin
from models.enums import LedgerEntryType


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model for tracking PO line balances.
    
    Maintains running balances of ordered, delivered, and invoiced quantities.
    """
    
    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_bl_po_line_id", "po_line_id"),
        Index("ix_bl_entry_type", "entry_type"),
        Index("ix_bl_reference_type", "reference_type"),
        Index("ix_bl_entry_date", "entry_date"),
        Index("ix_bl_created_at", "created_at"),
        {"schema": None},
    )
    
    # PO Line reference
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Entry identification
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    entry_number: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Reference documents
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    reference_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Entry date
    entry_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    # Quantities (for delivery and invoice entries)
    quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    # Amounts (for invoice entries)
    amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    # Running balance after this entry
    balance_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    balance_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    # Balance snapshot
    total_ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    total_delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    total_invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    total_invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # User tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="ledger_entries",
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger {self.entry_type.value} - {self.entry_number}>"
