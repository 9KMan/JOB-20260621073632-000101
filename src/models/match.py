// src/models/match.py
from sqlalchemy import Column, String, Numeric, DateTime, Integer, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class MatchStatus(str, enum.Enum):
    """Match status enumeration."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"


class MatchDecision(str, enum.Enum):
    """Match decision enumeration."""
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


class MatchType(str, enum.Enum):
    """Type of match performed."""
    INVOICE_TO_PO = "INVOICE_TO_PO"
    DN_TO_PO = "DN_TO_PO"
    INVOICE_TO_DN = "INVOICE_TO_DN"
    THREE_WAY = "THREE_WAY"


class Match(BaseModel):
    """Match model for storing matching results."""
    
    __tablename__ = "matches"
    
    match_type = Column(Enum(MatchType), nullable=False, index=True)
    
    # Document references
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True, index=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Scoring
    total_score = Column(Numeric(5, 4), nullable=False)
    line_level_score = Column(Numeric(5, 4), nullable=True)
    amount_score = Column(Numeric(5, 4), nullable=True)
    date_score = Column(Numeric(5, 4), nullable=True)
    
    # Financial comparison
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), nullable=True)
    
    # Quantities comparison
    po_quantity = Column(Numeric(15, 4), nullable=True)
    invoice_quantity = Column(Numeric(15, 4), nullable=True)
    dn_quantity = Column(Numeric(15, 4), nullable=True)
    quantity_variance = Column(Numeric(15, 4), nullable=True)
    
    # Status and decision
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING, nullable=False, index=True)
    decision = Column(Enum(MatchDecision), nullable=True, index=True)
    
    # Human review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Details stored as JSON
    line_level_details = Column(JSONB, nullable=True)
    match_confidence = Column(String(50), nullable=True)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="matches")
    delivery_note = relationship("DeliveryNote", back_populates="matches")
    purchase_order = relationship("PurchaseOrder", back_populates="matches")
    reviewed_by_user = relationship("User", back_populates="matches")
    
    def __repr__(self):
        return f"<Match {self.match_type} {self.status}>"
