# app/models/matching.py
"""Matching Result and Match Line Result models."""
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class MatchStatus(str, enum.Enum):
    """Matching result status enum."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class MatchDecision(str, enum.Enum):
    """Match decision enum."""

    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class MatchingResult(Base, TimestampMixin):
    """Matching Result model for 3-way matching."""

    __tablename__ = "matching_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    dn_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id"), nullable=True)
    
    # Match type: invoice_po, invoice_dn, dn_po, or three_way
    match_type = Column(String(20), nullable=False, index=True)
    
    # Overall match scores
    total_score = Column(Numeric(5, 4), default=0, nullable=False)
    line_score = Column(Numeric(5, 4), default=0, nullable=False)
    amount_score = Column(Numeric(5, 4), default=0, nullable=False)
    date_score = Column(Numeric(5, 4), default=0, nullable=False)
    
    # Match status and decision
    status = Column(String(20), default=MatchStatus.PENDING.value, nullable=False, index=True)
    decision = Column(String(20), nullable=True, index=True)
    
    # Amount comparisons
    invoice_amount = Column(Numeric(15, 2), default=0, nullable=False)
    po_amount = Column(Numeric(15, 2), default=0, nullable=True)
    dn_amount = Column(Numeric(15, 2), default=0, nullable=True)
    variance_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Variance details stored as JSON
    variance_details = Column(JSONB, nullable=True)
    
    # Confirmation
    confirmed_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    confirmed_at = Column(String(30), nullable=True)
    confirmation_notes = Column(Text, nullable=True)
    
    # Error/issue tracking
    error_message = Column(Text, nullable=True)
    warnings = Column(JSONB, nullable=True)

    # Relationships
    invoice = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="matching_results",
    )
    purchase_order = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="matched_invoices",
    )
    delivery_note = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="matched_delivery_notes",
    )
    confirmed_by_user = relationship(
        "User",
        foreign_keys=[confirmed_by],
        back_populates="matching_confirmations",
    )
    line_results = relationship(
        "MatchLineResult",
        back_populates="matching_result",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MatchingResult(id={self.id}, match_type={self.match_type}, score={self.total_score})>"


class MatchLineResult(Base, TimestampMixin):
    """Match Line Result model for line-level matching."""

    __tablename__ = "match_line_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matching_result_id = Column(
        UUID(as_uuid=True), ForeignKey("matching_results.id", ondelete="CASCADE"), nullable=False
    )
    invoice_line_id = Column(
        UUID(as_uuid=True), ForeignKey("invoice_lines.id"), nullable=True
    )
    po_line_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True
    )
    dn_line_id = Column(
        UUID(as_uuid=True), ForeignKey("delivery_note_lines.id"), nullable=True
    )
    
    # Match type for this line
    match_type = Column(String(20), nullable=False)
    
    # Line match score
    match_score = Column(Numeric(5, 4), default=0, nullable=False)
    
    # Product match details
    product_match = Column(String(20), default="none", nullable=False)  # exact, fuzzy, none
    quantity_match = Column(String(20), default="none", nullable=False)  # exact, partial, over, under, none
    amount_match = Column(String(20), default="none", nullable=False)  # exact, partial, over, under, none
    
    # Quantity comparisons
    invoice_quantity = Column(Numeric(15, 4), default=0, nullable=True)
    po_quantity = Column(Numeric(15, 4), default=0, nullable=True)
    dn_quantity = Column(Numeric(15, 4), default=0, nullable=True)
    quantity_variance = Column(Numeric(15, 4), default=0, nullable=True)
    
    # Amount comparisons
    invoice_line_amount = Column(Numeric(15, 2), default=0, nullable=True)
    po_line_amount = Column(Numeric(15, 2), default=0, nullable=True)
    dn_line_amount = Column(Numeric(15, 2), default=0, nullable=True)
    amount_variance = Column(Numeric(15, 2), default=0, nullable=True)
    
    # Match details as JSON
    match_details = Column(JSONB, nullable=True)
    matched_automatically = Column(String(20), nullable=True)

    # Relationships
    matching_result = relationship("MatchingResult", back_populates="line_results")
    invoice_line = relationship("InvoiceLine", back_populates="match_line_results")
    po_line = relationship("PurchaseOrderLine")
    dn_line = relationship("DeliveryNoteLine", back_populates="match_line_results")

    def __repr__(self) -> str:
        return f"<MatchLineResult(id={self.id}, match_score={self.match_score})>"
