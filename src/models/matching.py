// src/models/matching.py
"""Matching and balance resolution models."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.database import Base


class MatchStatus(str, enum.Enum):
    """Match result status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class MatchType(str, enum.Enum):
    """Match type enumeration."""

    INVOICE_PO = "invoice_po"
    INVOICE_DN = "invoice_dn"
    DN_PO = "dn_po"
    THREE_WAY = "three_way"


class BalanceType(str, enum.Enum):
    """Balance entry type enumeration."""

    INVOICE_BALANCE = "invoice_balance"
    PO_BALANCE = "po_balance"
    DN_BALANCE = "dn_balance"


class MatchResult(Base):
    """Match result model for tracking document matches."""

    __tablename__ = "match_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    match_type = Column(String(50), nullable=False, index=True)
    
    # Partner document references
    partner_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, index=True)
    third_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, index=True)
    
    # Matching scores
    line_level_score = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    amount_score = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    date_score = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    overall_score = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    
    # Match amounts
    matched_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    variance_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    variance_percentage = Column(Numeric(5, 4), nullable=False, default=Decimal("0.00"))
    
    # Matched quantities
    matched_quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))
    variance_quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))
    
    # Status and decision
    status = Column(String(50), nullable=False, default=MatchStatus.PENDING.value, index=True)
    decision = Column(String(50), nullable=True)  # AUTO_APPROVE, HUMAN_REVIEW, DISPUTE
    requires_review = Column(Boolean, default=False, nullable=False)
    
    # Variance details
    price_variance = Column(Numeric(15, 4), nullable=False, default=Decimal("0.0000"))
    quantity_variance = Column(Numeric(15, 4), nullable=False, default=Decimal("0.0000"))
    date_variance_days = Column(Integer, nullable=False, default=0)
    
    # Review information
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Metadata
    match_details = Column(Text, nullable=True)  # JSON string with detailed match info
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", foreign_keys=[document_id], back_populates="match_results")
    partner_document = relationship("Document", foreign_keys=[partner_document_id])
    third_document = relationship("Document", foreign_keys=[third_document_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    line_matches = relationship("LineMatch", back_populates="match_result", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_match_results_document_status", "document_id", "status"),
        Index("ix_match_results_partner", "partner_document_id"),
        Index("ix_match_results_score_status", "overall_score", "status"),
    )


class LineMatch(Base):
    """Line-level match details."""

    __tablename__ = "line_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_result_id = Column(UUID(as_uuid=True), ForeignKey("match_results.id"), nullable=False)
    
    # Source line
    source_line_id = Column(UUID(as_uuid=True), ForeignKey("document_lines.id"), nullable=False)
    source_product_code = Column(String(100), nullable=False)
    source_product_name = Column(String(255), nullable=False)
    
    # Matched line
    matched_line_id = Column(UUID(as_uuid=True), ForeignKey("document_lines.id"), nullable=True)
    matched_product_code = Column(String(100), nullable=True)
    matched_product_name = Column(String(255), nullable=True)
    
    # Match details
    is_exact_match = Column(Boolean, default=False, nullable=False)
    match_confidence = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    
    # Quantities
    source_quantity = Column(Numeric(15, 3), nullable=False)
    matched_quantity = Column(Numeric(15, 3), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False)
    
    # Variances
    quantity_variance = Column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))
    price_variance = Column(Numeric(15, 4), nullable=False, default=Decimal("0.0000"))
    variance_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    match_result = relationship("MatchResult", back_populates="line_matches")
    source_line = relationship("DocumentLine", foreign_keys=[source_line_id])
    matched_line = relationship("DocumentLine", foreign_keys=[matched_line_id])

    __table_args__ = (
        Index("ix_line_matches_result", "match_result_id"),
    )


class BalanceEntry(Base):
    """Balance tracking ledger for partial matches and splits."""

    __tablename__ = "balance_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance_type = Column(String(50), nullable=False, index=True)
    
    # Document references
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    document_number = Column(String(100), nullable=False)
    
    # PO reference for invoice/DN balances
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True, index=True)
    po_number = Column(String(100), nullable=True)
    
    # Balance amounts
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    balance_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Quantities
    original_quantity = Column(Numeric(15, 3), nullable=False)
    matched_quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0.000"))
    balance_quantity = Column(Numeric(15, 3), nullable=False)
    
    # Status
    is_cleared = Column(Boolean, default=False, nullable=False, index=True)
    cleared_at = Column(DateTime, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document")
    purchase_order = relationship("PurchaseOrder")

    __table_args__ = (
        Index("ix_balance_entries_document", "document_id", "balance_type", unique=True),
        Index("ix_balance_entries_po", "po_number", "balance_type"),
        Index("ix_balance_entries_open", "is_cleared", "balance_amount"),
    )


class MatchingSession(Base):
    """Batch matching session for tracking matching jobs."""

    __tablename__ = "matching_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_type = Column(String(50), nullable=False)  # MANUAL, AUTOMATIC, SCHEDULED
    status = Column(String(50), nullable=False, default="running")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Statistics
    total_documents = Column(Integer, nullable=False, default=0)
    matched_count = Column(Integer, nullable=False, default=0)
    pending_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    
    # Configuration
    auto_approve_threshold = Column(Numeric(5, 4), nullable=False)
    human_review_threshold = Column(Numeric(5, 4), nullable=False)
    
    # User
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Results summary
    results_summary = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    initiated_by_user = relationship("User")


# Import Integer for date_variance_days
from sqlalchemy import Integer
