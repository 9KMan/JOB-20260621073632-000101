# src/models/matching.py
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class MatchStatus(str, enum.Enum):
    """Match status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class MatchDecisionType(str, enum.Enum):
    """Match decision types."""
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"
    CONFIRM = "confirm"


class MatchingResult(BaseModel):
    """Matching Result model - stores results of 3-way matching."""

    __tablename__ = "matching_results"

    # Document references
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    dn_id = Column(String(36), ForeignKey("delivery_notes.id", ondelete="SET NULL"), nullable=True, index=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)

    # Match scores
    invoice_po_score = Column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000
    dn_po_score = Column(Numeric(5, 4), nullable=True)
    invoice_dn_score = Column(Numeric(5, 4), nullable=True)
    overall_score = Column(Numeric(5, 4), nullable=False, default=0)

    # Amount comparisons
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    po_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), default=0, nullable=False)
    variance_percentage = Column(Numeric(5, 2), default=0, nullable=False)

    # Match status
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.PENDING, nullable=False, index=True)
    match_type = Column(String(50), nullable=True)  # invoice_po, dn_po, invoice_dn, three_way
    notes = Column(Text, nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="matching_results")
    delivery_note = relationship("DeliveryNote", back_populates="matching_results")
    purchase_order = relationship("PurchaseOrder", back_populates="matched_invoices")
    decisions = relationship("MatchDecision", back_populates="matching_result", cascade="all, delete-orphan")
    balance_entries = relationship("BalanceLedger", back_populates="matching_result")


class MatchDecision(BaseModel):
    """Match Decision model - human confirmations feed into learning loop."""

    __tablename__ = "match_decisions"

    matching_result_id = Column(String(36), ForeignKey("matching_results.id", ondelete="CASCADE"), nullable=False, index=True)
    decided_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    decision_type = Column(SQLEnum(MatchDecisionType), nullable=False)
    decision_notes = Column(Text, nullable=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)

    # Relationships
    matching_result = relationship("MatchingResult", back_populates="decisions")
    user = relationship("User")


class BalanceLedger(BaseModel):
    """Balance Ledger model - tracks partial matches and balances."""

    __tablename__ = "balance_ledger"

    # Document references
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    dn_id = Column(String(36), ForeignKey("delivery_notes.id", ondelete="SET NULL"), nullable=True, index=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    matching_result_id = Column(String(36), ForeignKey("matching_results.id", ondelete="SET NULL"), nullable=True)

    # Balance tracking
    document_type = Column(String(20), nullable=False)  # invoice, dn, po
    document_number = Column(String(50), nullable=False)
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=0, nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    matching_result = relationship("MatchingResult", back_populates="balance_entries")
