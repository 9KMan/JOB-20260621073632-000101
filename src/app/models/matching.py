// src/app/models/matching.py
"""Matching result and decision models."""

from sqlalchemy import Column, String, Numeric, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from src.app.models.base import BaseModel


class MatchDecision(str, enum.Enum):
    """Match decision enumeration."""

    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class MatchType(str, enum.Enum):
    """Match type enumeration."""

    INVOICE_PO = "INVOICE_PO"
    DELIVERY_NOTE_PO = "DELIVERY_NOTE_PO"
    INVOICE_DELIVERY_NOTE = "INVOICE_DELIVERY_NOTE"
    THREE_WAY = "THREE_WAY"


class MatchResult(BaseModel):
    """Match result entity storing all matching outcomes."""

    __tablename__ = "match_results"

    # Document references
    invoice_id = Column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True
    )
    delivery_note_id = Column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True
    )
    purchase_order_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True
    )

    # Match metadata
    match_type = Column(String(20), nullable=False)
    match_score = Column(Numeric(5, 4), nullable=False)
    line_level_score = Column(Numeric(5, 4), nullable=True)
    amount_score = Column(Numeric(5, 4), nullable=True)
    date_score = Column(Numeric(5, 4), nullable=True)

    # Decision
    decision = Column(String(20), nullable=False, default=MatchDecision.PENDING.value)
    auto_processed = Column(String(10), nullable=False, default="FALSE")

    # Amount comparisons
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    po_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), nullable=True)

    # Quantity comparisons
    invoice_quantity = Column(Numeric(12, 3), nullable=True)
    po_quantity = Column(Numeric(12, 3), nullable=True)
    dn_quantity = Column(Numeric(12, 3), nullable=True)
    variance_quantity = Column(Numeric(12, 3), nullable=True)

    # Details
    details = Column(Text, nullable=True)
    discrepancy_notes = Column(Text, nullable=True)

    # Relationships
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    delivery_note = relationship("DeliveryNote", foreign_keys=[delivery_note_id])
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    confirmations = relationship(
        "HumanConfirmation", back_populates="match_result", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MatchResult(id={self.id}, match_type={self.match_type}, decision={self.decision})>"


class HumanConfirmation(BaseModel):
    """Human confirmation for disputed matches."""

    __tablename__ = "human_confirmations"

    match_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    confirmed_by = Column(String(255), nullable=False)
    confirmation_date = Column(String(50), nullable=False)
    original_decision = Column(String(20), nullable=False)
    new_decision = Column(String(20), nullable=False)
    comments = Column(Text, nullable=True)
    confidence_boost = Column(Numeric(5, 4), nullable=True)

    # Relationships
    match_result = relationship("MatchResult", back_populates="confirmations")

    def __repr__(self) -> str:
        return f"<HumanConfirmation(id={self.id}, new_decision={self.new_decision})>"
