// src/models/matching.py
"""
Matching models for 3-way matching engine
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from decimal import Decimal

from src.models.base import UUIDModel, TimestampModel, SoftDeleteModel


class MatchRecord(UUIDModel, TimestampModel, SoftDeleteModel):
    """Match record capturing the result of 3-way matching"""
    __tablename__ = "match_records"
    
    # Document references
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=True,
        index=True
    )
    delivery_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id"),
        nullable=True,
        index=True
    )
    
    # Match decision
    MATCH_CONFIRMED = "confirmed"
    MATCH_PENDING = "pending"
    MATCH_REJECTED = "rejected"
    
    match_status = Column(
        String(50),
        default=MATCH_PENDING,
        nullable=False,
        index=True
    )
    
    # Decision routing
    DECISION_AUTO_APPROVE = "auto_approve"
    DECISION_HUMAN_REVIEW = "human_review"
    DECISION_DISPUTE = "dispute"
    
    decision = Column(String(50), nullable=True, index=True)
    
    # Scoring breakdown
    line_match_score = Column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    amount_match_score = Column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    date_match_score = Column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    overall_score = Column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    
    # Match type
    MATCH_3_WAY = "3_way"
    MATCH_2_WAY_PO_INVOICE = "2_way_po_invoice"
    MATCH_2_WAY_PO_DN = "2_way_po_dn"
    MATCH_2_WAY_INVOICE_DN = "2_way_invoice_dn"
    
    match_type = Column(String(50), default=MATCH_3_WAY, nullable=False)
    
    # Variance details
    amount_variance = Column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    quantity_variance = Column(Numeric(15, 3), default=Decimal("0"), nullable=False)
    
    # Variance reason
    VARIANCE_NONE = "none"
    VARIANCE_PRICE = "price"
    VARIANCE_QUANTITY = "quantity"
    VARIANCE_PARTIAL = "partial"
    VARIANCE_OVER = "over"
    VARIANCE_UNDER = "under"
    
    variance_reason = Column(String(50), default=VARIANCE_NONE, nullable=True)
    
    # Detailed match results (JSON)
    line_match_details = Column(JSONB, nullable=True)
    match_notes = Column(Text, nullable=True)
    
    # Human review
    confirmed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    review_comments = Column(Text, nullable=True)
    
    # Relationships
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="match_records"
    )
    invoice = relationship(
        "Invoice",
        back_populates="match_records"
    )
    delivery_note = relationship(
        "DeliveryNote",
        back_populates="match_records"
    )
    confirmed_by_user = relationship(
        "User",
        back_populates="confirmed_matches",
        foreign_keys=[confirmed_by]
    )
    
    def __repr__(self):
        return f"<MatchRecord {self.id} - {self.match_status}>"


class BalanceLedger(UUIDModel, TimestampModel):
    """
    Balance tracking ledger for partial matches
    Tracks outstanding balances across PO, Invoice, and Delivery Note
    """
    __tablename__ = "balance_ledger"
    
    # Document reference (polymorphic - can reference any document type)
    document_type = Column(String(50), nullable=False)  # 'po', 'invoice', 'dn'
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # PO reference for grouping
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True
    )
    
    # Amount tracking
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    balance_amount = Column(Numeric(15, 2), nullable=False)
    
    # Reference to match record
    match_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("match_records.id"),
        nullable=True
    )
    
    # Status
    STATUS_OPEN = "open"
    STATUS_PARTIAL = "partial"
    STATUS_CLOSED = "closed"
    
    status = Column(String(50), default=STATUS_OPEN, nullable=False)
    
    # Relationships
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="balance_records"
    )
    invoice = relationship(
        "Invoice",
        back_populates="balance_records"
    )
    delivery_note = relationship(
        "DeliveryNote",
        back_populates="balance_records"
    )
    
    def __repr__(self):
        return f"<BalanceLedger {self.document_type} - Balance: {self.balance_amount}>"


class MatchLearningHistory(UUIDModel, TimestampModel):
    """
    Learning history for improving future matches
    Records human confirmations to improve matching algorithm
    """
    __tablename__ = "match_learning_history"
    
    match_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("match_records.id"),
        nullable=False
    )
    
    # Original vs confirmed decision
    original_match_status = Column(String(50), nullable=False)
    confirmed_match_status = Column(String(50), nullable=False)
    confirmed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=False)
    
    # Feedback details
    feedback_type = Column(String(50), nullable=True)
    feedback_notes = Column(Text, nullable=True)
    
    # Document identifiers for lookup
    po_number = Column(String(50), nullable=True, index=True)
    invoice_number = Column(String(50), nullable=True, index=True)
    dn_number = Column(String(50), nullable=True, index=True)
    
    def __repr__(self):
        return f"<MatchLearningHistory {self.id}>"
