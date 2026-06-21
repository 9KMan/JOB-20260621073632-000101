// src/models/balance_ledger.py
"""Balance Ledger for tracking partial matches and balances."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.models.base import Base, BaseModel


class BalanceLedger(Base, BaseModel):
    """Balance Ledger - tracks remaining balances across all document types."""
    __tablename__ = "balance_ledger"

    # Document references
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    dn_id = Column(String(36), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Reference to line if applicable
    po_line_id = Column(String(36), ForeignKey("purchase_order_lines.id", ondelete="CASCADE"), nullable=True)
    invoice_line_id = Column(String(36), ForeignKey("invoice_lines.id", ondelete="CASCADE"), nullable=True)
    dn_line_id = Column(String(36), ForeignKey("delivery_note_lines.id", ondelete="CASCADE"), nullable=True)
    
    # Match result that created this balance
    match_result_id = Column(String(36), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True)
    
    # Document type for this balance entry
    document_type = Column(String(20), nullable=False)  # PO, INVOICE, DN
    
    # Original amounts
    original_amount = Column(Numeric(15, 2), nullable=False)
    original_quantity = Column(Numeric(15, 4), nullable=False)
    
    # Balance tracking
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    matched_quantity = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    remaining_quantity = Column(Numeric(15, 4), nullable=False)
    
    # Balance type
    balance_type = Column(String(20), default="open", nullable=False)  # open, partial, closed
    
    # Status
    is_active = Column(String(1), default="Y", nullable=False)  # Y, N
    
    # Metadata
    notes = Column(Text, nullable=True)
    closed_reason = Column(String(100), nullable=True)
    
    # Relationships
    purchase_order: Optional["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="balance_entries",
    )
    invoice: Optional["Invoice"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="balance_entries",
    )
    delivery_note: Optional["DeliveryNote"] = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type} - {self.remaining_amount}>"

    def update_balance(self, amount: Decimal, quantity: Decimal) -> None:
        """Update the balance with matched amount and quantity."""
        self.matched_amount += amount
        self.matched_quantity += quantity
        self.remaining_amount = self.original_amount - self.matched_amount
        self.remaining_quantity = self.original_quantity - self.matched_quantity
        
        if self.remaining_amount <= 0 and self.remaining_quantity <= 0:
            self.balance_type = "closed"
        elif self.matched_amount > 0 or self.matched_quantity > 0:
            self.balance_type = "partial"

    @property
    def is_fully_matched(self) -> bool:
        """Check if balance is fully matched."""
        return self.balance_type == "closed"

    @property
    def is_partially_matched(self) -> bool:
        """Check if balance is partially matched."""
        return self.balance_type == "partial"
