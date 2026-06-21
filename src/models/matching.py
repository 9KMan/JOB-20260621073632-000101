// src/models/matching.py
"""Matching record and decision models."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class MatchType(str, Enum):
    """Type of match between documents."""
    PO_INVOICE = "po_invoice"
    PO_DELIVERY = "po_delivery"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class MatchStatus(str, Enum):
    """Status of the matching record."""
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    DISPUTED = "disputed"


class MatchDecision(str, Enum):
    """Decision outcome from matching engine."""
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    REJECTED = "rejected"


class MatchConfidenceLevel(str, Enum):
    """Confidence level of the match."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MatchingRecord(BaseModel):
    """Matching record model - tracks all matches between documents."""

    __tablename__ = "matching_records"

    # Match type and status
    match_type: str = Column(String(20), nullable=False)
    status: str = Column(String(20), default=MatchStatus.PENDING.value, nullable=False)
    decision: Optional[str] = Column(String(20), nullable=True)

    # Confidence and scores
    overall_score: Decimal = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    line_level_score: Decimal = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    amount_score: Decimal = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    date_score: Decimal = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    confidence_level: str = Column(String(10), default=MatchConfidenceLevel.LOW.value, nullable=False)

    # Document references
    purchase_order_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    invoice_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    delivery_note_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id"), nullable=True)

    # Matched amounts
    po_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    invoice_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    delivery_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    matched_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Variance details
    quantity_variance: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    amount_variance: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    price_variance: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    date_variance_days: int = Column(Numeric(5, 0), default=0, nullable=False)

    # Detailed match results as JSON
    line_match_details: Optional[dict] = Column(JSONB, nullable=True)
    variance_details: Optional[dict] = Column(JSONB, nullable=True)

    # Review information
    review_notes: Optional[str] = Column(Text, nullable=True)
    rejection_reason: Optional[str] = Column(Text, nullable=True)
    confirmed_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Learning loop - feedback from human confirmation
    feedback_data: Optional[dict] = Column(JSONB, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    delivery_note = relationship("DeliveryNote", foreign_keys=[delivery_note_id])
    confirmed_by_user = relationship("User", foreign_keys=[confirmed_by_id], back_populates="matching_confirmations")

    def __repr__(self) -> str:
        return f"<MatchingRecord {self.id} - {self.match_type} - {self.status}>"
