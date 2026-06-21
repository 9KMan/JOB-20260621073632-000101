# app/models/balance.py
# app/models/balance.py
"""Balance Ledger model for tracking partial matches and balances."""
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class BalanceType(str, enum.Enum):
    """Balance type enum."""

    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    PURCHASE_ORDER = "purchase_order"


class BalanceStatus(str, enum.Enum):
    """Balance status enum."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    DISPUTED = "disputed"
    WRITE_OFF = "write_off"


class BalanceLedger(Base, TimestampMixin):
    """Balance Ledger model for tracking partial matches across documents."""

    __tablename__ = "balance_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Document references
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    dn_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id"), nullable=True)
    
    # Balance type (which document this balance belongs to)
    balance_type = Column(String(20), nullable=False, index=True)
    
    # Original and remaining amounts
    original_amount = Column(Numeric(15, 2), default=0, nullable=False)
    matched_amount = Column(Numeric(15, 2), default=0, nullable=False)
    remaining_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Status
    status = Column(String(20), default=BalanceStatus.OPEN.value, nullable=False, index=True)
    
    # Related matching result
    matching_result_id = Column(
        UUID(as_uuid=True), ForeignKey("matching_results.id"), nullable=True
    )
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Reconciliation
    reconciled_at = Column(String(30), nullable=True)
    reconciled_by = Column(String(255), nullable=True)

    # Relationships
    invoice = relationship("Invoice")
    purchase_order = relationship("PurchaseOrder")
    delivery_note = relationship("DeliveryNote")
    matching_result = relationship("MatchingResult")

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, balance_type={self.balance_type}, remaining={self.remaining_amount})>"

    def update_balance(self, matched_amount: float) -> None:
        """Update balance after a match."""
        self.matched_amount = self.matched_amount + matched_amount
        self.remaining_amount = self.original_amount - self.matched_amount
        
        if self.remaining_amount <= 0:
            self.status = BalanceStatus.FULLY_MATCHED.value
        elif self.matched_amount > 0:
            self.status = BalanceStatus.PARTIALLY_MATCHED.value
