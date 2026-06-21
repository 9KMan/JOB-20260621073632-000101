// src/models/matching.py
"""Matching result models."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric, DateTime, Text, Enum, ForeignKey, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MatchStatus(str, enum.Enum):
    """Match status enumeration."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


class MatchType(str, enum.Enum):
    """Match type enumeration."""

    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY_NOTE = "PO_DELIVERY_NOTE"
    INVOICE_DELIVERY_NOTE = "INVOICE_DELIVERY_NOTE"
    THREE_WAY = "THREE_WAY"


class MatchResult(Base, TimestampMixin):
    """Match Result model storing all match outcomes."""

    __tablename__ = "match_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    invoice_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    match_type: Mapped[MatchType] = mapped_column(Enum(MatchType), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
    )
    
    # Overall score
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    
    # Component scores
    line_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    amount_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    date_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    
    # Amount differences
    po_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    invoice_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    delivery_note_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    amount_variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Quantity differences
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    invoice_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    delivery_note_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    quantity_variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    
    # Decision
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Human review
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Match details (JSON)
    line_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Relationships
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="match_results",
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
        back_populates="match_results",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="matched_invoices",
    )

    __table_args__ = (
        Index("ix_match_results_status", "status"),
        Index("ix_match_results_match_type", "match_type"),
        Index("ix_match_results_po_invoice", "po_id", "invoice_id"),
        Index("ix_match_results_po_dn", "po_id", "delivery_note_id"),
    )


class MatchScore(Base, TimestampMixin):
    """Detailed line-level match scores."""

    __tablename__ = "match_scores"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    match_result_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Line references
    po_line_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    invoice_line_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    delivery_note_line_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Product match
    product_code_match: Mapped[bool] = mapped_column(nullable=False, default=False)
    
    # Quantity match
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    matched_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    quantity_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    
    # Amount match
    po_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    matched_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    amount_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    
    # Combined score for this line
    line_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    
    # Status
    is_matched: Mapped[bool] = mapped_column(nullable=False, default=False)
    variance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="scores",
    )
