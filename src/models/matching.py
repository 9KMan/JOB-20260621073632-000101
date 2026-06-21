# src/models/matching.py
"""Matching Record model for 3-way matching."""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class MatchingRecord(BaseModel):
    """Matching Record model for tracking document matches."""

    __tablename__ = "matching_records"

    # Document references
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Matching scores
    line_level_score = Column(Numeric(5, 2), default=0, nullable=False)
    amount_score = Column(Numeric(5, 2), default=0, nullable=False)
    date_score = Column(Numeric(5, 2), default=0, nullable=False)
    overall_score = Column(Numeric(5, 2), default=0, nullable=False)

    # Matching weights
    line_weight = Column(Numeric(5, 2), default=70, nullable=False)
    amount_weight = Column(Numeric(5, 2), default=20, nullable=False)
    date_weight = Column(Numeric(5, 2), default=10, nullable=False)

    # Match details
    match_type = Column(String(50), nullable=False, index=True)  # PO-INV, PO-DN, INV-DN, 3-WAY
    match_status = Column(String(50), default="pending", nullable=False, index=True)  # confirmed, pending, rejected
    decision = Column(String(50), nullable=False, index=True)  # AUTO_APPROVE, HUMAN_REVIEW, DISPUTE
    decision_reason = Column(Text, nullable=True)

    # Amount comparison
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    delivery_note_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), default=0, nullable=False)

    # Metadata
    match_metadata = Column(JSONB, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="matching_records")
    invoice = relationship("Invoice", back_populates="matching_records")
    delivery_note = relationship("DeliveryNote", back_populates="matching_records")
    line_matches = relationship("MatchingLine", back_populates="matching_record", cascade="all, delete-orphan")
