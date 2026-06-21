// models/matching.py
"""Matching models for 3-way matching engine."""
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, DateTime, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from models.base import BaseModel


class MatchStatus(enum.Enum):
    """Matching status enum."""
    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    REJECTED = "rejected"


class MatchDecision(enum.Enum):
    """Match decision enum for routing."""
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class MatchingRecord(BaseModel):
    """Main matching record that links PO, Invoice, and Delivery Note."""
    
    __tablename__ = "matching_records"
    
    # Document references
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=True)
    dn_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="RESTRICT"), nullable=True)
    
    # Match metadata
    match_type = Column(String(50), nullable=False)  # PO_INVOICE, PO_DN, INVOICE_DN, THREE_WAY
    status = Column(String(50), default=MatchStatus.PENDING.value, nullable=False, index=True)
    decision = Column(String(50), nullable=True)  # From MatchDecision
    match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)  # 0.0000 to 1.0000
    
    # Amount matching
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_percentage = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    
    # Date matching
    invoice_date_match = Column(Boolean, default=False, nullable=False)
    delivery_date_match = Column(Boolean, default=False, nullable=False)
    date_variance_days = Column(Integer, default=0, nullable=False)
    
    # Approval workflow
    matched_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    matched_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Score breakdown
    line_level_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    amount_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    date_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id], back_populates="matched_invoices")
    invoice = relationship("Invoice", foreign_keys=[invoice_id], back_populates="matched_records")
    delivery_note = relationship("DeliveryNote", foreign_keys=[dn_id], back_populates="matched_records")
    matched_by_user = relationship("User", foreign_keys=[matched_by_id])
    confirmed_by_user = relationship("User", foreign_keys=[confirmed_by_id])
    lines = relationship("MatchingLine", back_populates="matching_record", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MatchingRecord(id={self.id}, po_id={self.po_id}, invoice_id={self.invoice_id}, decision={self.decision})>"


class MatchingLine(BaseModel):
    """Line-level matching details."""
    
    __tablename__ = "matching_lines"
    
    matching_record_id = Column(UUID(as_uuid=True), ForeignKey("matching_records.id", ondelete="CASCADE"), nullable=False)
    
    # Line references
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    invoice_line_id = Column(UUID(as_uuid=True), ForeignKey("invoice_lines.id", ondelete="SET NULL"), nullable=True)
    dn_line_id = Column(UUID(as_uuid=True), ForeignKey("delivery_note_lines.id", ondelete="SET NULL"), nullable=True)
    
    # Quantities
    po_quantity = Column(Numeric(15, 3), nullable=True)
    invoice_quantity = Column(Numeric(15, 3), nullable=True)
    dn_quantity = Column(Numeric(15, 3), nullable=True)
    matched_quantity = Column(Numeric(15, 3), nullable=False)
    variance_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    
    # Amounts
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    matched_amount = Column(Numeric(15, 2), nullable=False)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Match status
    is_matched = Column(Boolean, default=False, nullable=False)
    match_confidence = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    
    # Description match
    description_similarity = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    item_code_match = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    matching_record = relationship("MatchingRecord", back_populates="lines")
    po_line = relationship("PurchaseOrderLine", foreign_keys=[po_line_id])
    invoice_line = relationship("InvoiceLine", foreign_keys=[invoice_line_id])
    dn_line = relationship("DeliveryNoteLine", foreign_keys=[dn_line_id])
    
    def __repr__(self) -> str:
        return f"<MatchingLine(id={self.id}, matching_record_id={self.matching_record_id})>"
