// src/models/match.py
"""
FinaRo AP Automation Core Engine
Matching Models
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote


class MatchStatus(str, Enum):
    """Match status enumeration."""
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    UNMATCHED = "UNMATCHED"


class MatchDecision(str, Enum):
    """Match decision enumeration for routing."""
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"
    DISPUTE = "DISPUTE"


class MatchType(str, Enum):
    """Type of match being performed."""
    PO_INVOICE = "PO_INVOICE"
    PO_DN = "PO_DN"
    INVOICE_DN = "INVOICE_DN"
    THREE_WAY = "THREE_WAY"


class Match(BaseModel):
    """
    Match model representing matches between documents.
    Supports 2-way (PO↔Invoice, PO↔DN, Invoice↔DN) and 3-way matches.
    """
    __tablename__ = "matches"
    
    # Match Identification
    match_number = Column(String(50), unique=True, nullable=False, index=True)
    match_type = Column(
        String(20),
        nullable=False,
        index=True
    )
    
    # Document References
    po_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    dn_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Match Status
    status = Column(
        String(20),
        default=MatchStatus.PENDING.value,
        nullable=False,
        index=True
    )
    decision = Column(
        String(20),
        default=MatchDecision.HUMAN_REVIEW.value,
        nullable=False,
        index=True
    )
    
    # Scoring
    total_score = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    line_score = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    amount_score = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    date_score = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    
    # Amount Analysis
    po_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    invoice_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    dn_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    variance_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Quantity Analysis
    quantity_po = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    quantity_invoice = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    quantity_dn = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    variance_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    
    # Matched Line Details (JSON for flexibility)
    matched_lines = Column(JSON, nullable=True)
    
    # Variance Details
    variance_reason = Column(Text, nullable=True)
    variance_notes = Column(Text, nullable=True)
    
    # Approval Information
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    # Human Review
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comments = Column(Text, nullable=True)
    
    # Dispute Information
    disputed_by = Column(UUID(as_uuid=True), nullable=True)
    disputed_at = Column(DateTime, nullable=True)
    dispute_reason = Column(Text, nullable=True)
    dispute_resolution = Column(Text, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    po: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="matches_as_anchor",
        lazy="selectin"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="matches",
        lazy="selectin"
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="matches",
        lazy="selectin"
    )
    results: Mapped[List["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="match",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Match(id={self.id}, match_number='{self.match_number}', status='{self.status}')>"
    
    def determine_decision(self, auto_approve_threshold: float = 0.95) -> MatchDecision:
        """
        Determine the match decision based on scores.
        
        Args:
            auto_approve_threshold: Score threshold for automatic approval
            
        Returns:
            MatchDecision based on the match score
        """
        if float(self.total_score) >= auto_approve_threshold:
            return MatchDecision.AUTO_APPROVED
        elif float(self.total_score) >= 0.70:
            return MatchDecision.HUMAN_REVIEW
        else:
            return MatchDecision.REJECTED
    
    @property
    def is_confirmed(self) -> bool:
        """Check if match is confirmed (auto-approved or approved by human)."""
        return self.decision in (
            MatchDecision.AUTO_APPROVED.value,
            MatchDecision.HUMAN_REVIEW.value
        ) and self.status == MatchStatus.MATCHED.value
    
    @property
    def is_pending(self) -> bool:
        """Check if match is pending review."""
        return self.status == MatchStatus.PENDING.value and self.decision == MatchDecision.HUMAN_REVIEW.value
    
    @property
    def is_rejected(self) -> bool:
        """Check if match is rejected."""
        return self.decision == MatchDecision.REJECTED.value


class MatchResult(BaseModel):
    """
    Match Result model for detailed line-level matching results.
    Provides detailed breakdown of matches at the line item level.
    """
    __tablename__ = "match_results"
    
    # Foreign Key
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Line References (flexible mapping)
    po_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    invoice_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    dn_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Line Product Information
    product_code = Column(String(50), nullable=True)
    product_name = Column(String(255), nullable=True)
    
    # Match Status at Line Level
    status = Column(
        String(20),
        default=MatchStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # Quantity Analysis
    po_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    invoice_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    dn_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    matched_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    variance_quantity = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    
    # Amount Analysis
    po_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    invoice_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    dn_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    variance_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Match Score
    score = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    
    # Match Type for this line
    match_type = Column(String(20), nullable=True)
    
    # Variance Details
    variance_reason = Column(Text, nullable=True)
    variance_tolerance = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationship
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="results"
    )
    
    def __repr__(self) -> str:
        return f"<MatchResult(id={self.id}, match_id={self.match_id}, status='{self.status}')>"
    
    @property
    def match_percentage(self) -> Decimal:
        """Calculate match percentage for this line."""
        if self.po_amount > 0:
            return (self.matched_amount / self.po_amount) * 100
        return Decimal('0.00')
    
    @property
    def is_within_tolerance(self) -> bool:
        """Check if variance is within tolerance."""
        return abs(self.variance_amount) <= self.variance_tolerance * self.po_amount
