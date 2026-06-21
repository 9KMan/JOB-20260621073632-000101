// src/models/matching.py
"""Matching and balance tracking models."""
from decimal import Decimal

from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class MatchType(str, enum.Enum):
    """Type of match between documents."""
    INVOICE_TO_PO = "invoice_to_po"
    DN_TO_PO = "dn_to_po"
    INVOICE_TO_DN = "invoice_to_dn"
    THREE_WAY = "three_way"


class MatchStatus(str, enum.Enum):
    """Match record status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class MatchRecord(BaseModel):
    """Record of a match between documents."""

    __tablename__ = "match_records"

    match_type = Column(SQLEnum(MatchType), nullable=False, index=True)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.PENDING, nullable=False, index=True)

    # Document references
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    dn_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id"), nullable=True)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)

    # Match scores (0.0 to 1.0)
    line_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    amount_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    date_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    total_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    # Matched amounts
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    po_amount = Column(Numeric(15, 2), nullable=True)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Variance details
    quantity_variance = Column(Numeric(15, 3), nullable=True)
    amount_variance = Column(Numeric(15, 2), nullable=True)
    variance_reason = Column(Text, nullable=True)

    # Matched line details
    matched_line_details = Column("matched_line_details", JSONB, nullable=True)

    # Decision info
    decision = Column(SQLEnum("MatchDecision"), nullable=True)
    decision_notes = Column(Text, nullable=True)

    # Relationships
    invoice = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="match_records",
    )
    delivery_note = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="match_records",
    )
    purchase_order = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="matched_invoices",
    )
    cross_references = relationship(
        "CrossReference",
        back_populates="match_record",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MatchDecision(str, enum.Enum):
    """Match decision outcomes."""
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class BalanceLedger(BaseModel):
    """Ledger for tracking partial matches and balances."""

    __tablename__ = "balance_ledger"

    # Document reference
    document_type = Column(String(20), nullable=False, index=True)  # invoice, dn, po
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_number = Column(String(100), nullable=False, index=True)

    # Balance tracking
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    pending_amount = Column(Numeric(15, 2), nullable=False)
    balance = Column(Numeric(15, 2), nullable=False)

    # Reference to match record
    match_record_id = Column(UUID(as_uuid=True), ForeignKey("match_records.id"), nullable=True)

    # Status
    is_settled = Column(Integer, default=0, nullable=False)  # 0=pending, 1=settled

    # Relationships
    match_record = relationship("MatchRecord")


class CrossReference(BaseModel):
    """Cross-reference table for human confirmations (learning loop)."""

    __tablename__ = "cross_references"

    match_record_id = Column(UUID(as_uuid=True), ForeignKey("match_records.id"), nullable=False)
    
    # Document info
    document_type = Column(String(20), nullable=False)  # invoice, dn, po
    document_id = Column(UUID(as_uuid=True), nullable=False)
    document_number = Column(String(100), nullable=False)
    
    # Match info at time of confirmation
    matched_against_type = Column(String(20), nullable=False)
    matched_against_id = Column(UUID(as_uuid=True), nullable=False)
    matched_against_number = Column(String(100), nullable=False)
    
    # Confirmation details
    confirmed = Column(Integer, default=0, nullable=False)  # 0=rejected, 1=confirmed
    confirmation_notes = Column(Text, nullable=True)
    confirmed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(Text, nullable=True)

    # Feature values used for matching (for learning)
    feature_vector = Column("feature_vector", JSONB, nullable=True)

    # Relationships
    match_record = relationship("MatchRecord", back_populates="cross_references")
    confirmed_by_user = relationship("User", back_populates="match_decisions")
