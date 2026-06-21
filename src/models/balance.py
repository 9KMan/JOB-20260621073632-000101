// src/models/balance.py
from sqlalchemy import Column, String, Numeric, Integer, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class BalanceType(str, enum.Enum):
    """Balance entry type."""
    PO_OPEN = "PO_OPEN"
    PO_RETAINED = "PO_RETAINED"
    INVOICE_OPEN = "INVOICE_OPEN"
    INVOICE_RETAINED = "INVOICE_RETAINED"
    DN_OPEN = "DN_OPEN"
    DN_RETAINED = "DN_RETAINED"


class BalanceEntry(BaseModel):
    """Balance ledger for tracking partial matches."""
    
    __tablename__ = "balance_entries"
    
    balance_type = Column(Enum(BalanceType), nullable=False, index=True)
    
    # Document references
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Balance tracking
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False, default=0)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    
    # Line-level tracking
    po_line_id = Column(UUID(as_uuid=True), nullable=True)
    invoice_line_id = Column(UUID(as_uuid=True), nullable=True)
    dn_line_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Metadata
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="balance_entries")
    delivery_note = relationship("DeliveryNote", back_populates="balance_entries")
    match = relationship("Match")
    
    def __repr__(self):
        return f"<BalanceEntry {self.balance_type} remaining={self.remaining_amount}>"
