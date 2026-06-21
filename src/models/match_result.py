# src/models/match_result.py
"""Match Result model for 3-way matching."""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class MatchResult(Base, UUIDMixin, TimestampMixin):
    """Match Result model for 3-way matching between PO, Invoice, and Delivery Note."""
    
    __tablename__ = "match_results"
    
    # Document references
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Match type: PO_INVOICE, PO_DN, INVOICE_DN, THREE_WAY
    match_type = Column(String(20), nullable=False, index=True)
    
    # Match status: PENDING, CONFIRMED, REJECTED
    match_status = Column(String(20), default="PENDING", nullable=False, index=True)
    
    # Confidence score (0-100)
    confidence_score = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    
    # Match decision: AUTO_APPROVE, HUMAN_REVIEW, DISPUTE
    decision = Column(String(20), nullable=True, index=True)
    
    # Matched amounts
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Match date
    match_date = Column(Date, nullable=False)
    
    # Decision made date
    decision_date = Column(Date, nullable=True)
    decided_by = Column(String(255), nullable=True)
    
    # Detailed match breakdown
    line_level_matches = Column(JSON, nullable=True)
    match_details = Column(JSON, nullable=True)
    
    # Notes and comments
    notes = Column(Text, nullable=True)
    dispute_reason = Column(Text, nullable=True)
    
    # Human review fields
    reviewer_comments = Column(Text, nullable=True)
    reviewed_at = Column(Date, nullable=True)
    
    # Relationships
    purchase_order = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
        back_populates="matched_invoices",
    )
    invoice = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="matched_pos",
    )
    delivery_note = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
        back_populates="matched_pos",
    )
    line_items = relationship(
        "MatchLineItem",
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<MatchResult(id={self.id}, match_type={self.match_type}, decision={self.decision})>"
