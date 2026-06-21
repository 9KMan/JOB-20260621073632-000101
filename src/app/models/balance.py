// src/app/models/balance.py
"""
Balance Ledger model for tracking partial matches.
"""
from decimal import Decimal
from enum import Enum
from datetime import date

from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class BalanceType(str, Enum):
    """Balance type enumeration."""
    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class BalanceLedger(Base, UUIDPrimaryKey, TimestampMixin):
    """Ledger for tracking balances across partial matches."""

    __tablename__ = "balance_ledger"

    # Document reference
    document_type = Column(String(20), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_number = Column(String(50), nullable=False, index=True)
    
    # Balance info
    balance_type = Column(String(20), nullable=False, index=True)  # INVOICE, DELIVERY_NOTE, PURCHASE_ORDER
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    original_quantity = Column(Numeric(15, 3), nullable=False)
    matched_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    remaining_quantity = Column(Numeric(15, 3), nullable=False)
    
    # Reference to PO (for context)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True)
    po_number = Column(String(50), nullable=True, index=True)
    
    # Status
    is_settled = Column(String(10), default="open", nullable=False, index=True)  # open, partial, settled
    settled_at = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder")

    __table_args__ = (
        Index("ix_balance_document", "document_type", "document_id"),
        Index("ix_balance_po", "po_id", "is_settled"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}:{self.document_number} - {self.remaining_amount}>"

    @property
    def is_fully_settled(self) -> bool:
        """Check if balance is fully settled."""
        return self.is_settled == "settled" and self.remaining_amount == Decimal("0.00")

    @property
    def settlement_percentage(self) -> Decimal:
        """Get settlement percentage."""
        if self.original_amount == Decimal("0.00"):
            return Decimal("0.00")
        return (self.matched_amount / self.original_amount) * Decimal("100.00")
