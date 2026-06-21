# src/app/models/matching.py
"""Matching models for 3-way matching engine."""
import uuid
import decimal
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Numeric, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote
    from src.app.models.user import User


class MatchDecision:
    """Match decision constants."""
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    
    # Routing actions
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


class MatchType:
    """Type of match between documents."""
    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY = "PO_DELIVERY"
    INVOICE_DELIVERY = "INVOICE_DELIVERY"
    THREE_WAY = "THREE_WAY"


class MatchResult(BaseModel):
    """Result of matching operation between documents."""
    
    __tablename__ = "match_results"
    
    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Match metadata
    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    
    # Scoring
    overall_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    line_level_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    amount_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    date_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    # Decision
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    
    routing_action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    # Amount differences
    po_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    invoice_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    delivery_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    amount_difference: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    amount_difference_percentage: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    # Quantity differences
    po_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    invoice_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    delivery_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    quantity_difference: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    
    # Detailed scoring breakdown (JSON for flexibility)
    scoring_details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Line-level match results (JSON for flexibility)
    line_matches: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Review information
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    is_auto_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Flag for manual review required
    requires_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="match_results",
        foreign_keys=[purchase_order_id],
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="match_results",
        foreign_keys=[invoice_id],
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="match_results",
        foreign_keys=[delivery_note_id],
    )
    
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="match_results",
        foreign_keys=[reviewed_by],
    )
    
    scores: Mapped[List["MatchScore"]] = relationship(
        "MatchScore",
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    
    def determine_routing_action(self, auto_approve_threshold: float, human_review_threshold: float) -> str:
        """
        Determine the routing action based on the decision and score.
        
        Args:
            auto_approve_threshold: Score threshold for auto-approval
            human_review_threshold: Score threshold for human review
            
        Returns:
            Routing action: AUTO_APPROVE, HUMAN_REVIEW, or DISPUTE
        """
        if self.decision == MatchDecision.CONFIRMED and float(self.overall_score) >= auto_approve_threshold:
            self.routing_action = MatchDecision.AUTO_APPROVE
        elif self.decision in [MatchDecision.CONFIRMED, MatchDecision.PENDING] and float(self.overall_score) >= human_review_threshold:
            self.routing_action = MatchDecision.HUMAN_REVIEW
        else:
            self.routing_action = MatchDecision.DISPUTE
            self.requires_review = True
        
        return self.routing_action
    
    def __repr__(self) -> str:
        return f"<MatchResult(id={self.id}, type={self.match_type}, score={self.overall_score}, decision={self.decision})>"


class MatchScore(BaseModel):
    """
    Individual scoring components for a match.
    Provides detailed breakdown of matching criteria.
    """
    
    __tablename__ = "match_scores"
    
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    criteria_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    criteria_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    weight: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    weighted_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="scores",
    )
    
    def __repr__(self) -> str:
        return f"<MatchScore(id={self.id}, criteria={self.criteria_name}, score={self.score})>"
