// src/models/matching.py
"""Matching models for 3-way matching engine."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class MatchStatus(str, Enum):
    """Match status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class MatchType(str, Enum):
    """Match type enumeration."""
    PO_INVOICE = "po_invoice"
    PO_DELIVERY = "po_delivery"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class MatchResult(Base):
    """Match result model storing match analysis."""

    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Match type
    match_type: Mapped[MatchType] = mapped_column(
        SQLEnum(MatchType, name="match_type_enum"),
        nullable=False,
        index=True,
    )
    
    # Match status
    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status_enum"),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Matched documents
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Scoring
    total_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    line_level_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    amount_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    date_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    # Amount analysis
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    delivery_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Matched line items count
    total_line_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    matched_line_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    partial_line_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    unmatched_line_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Decision
    decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Audit
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    line_items = relationship(
        "MatchLineItem",
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    confirmations = relationship(
        "ConfirmationRecord",
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    purchase_order = relationship(
        "Document",
        foreign_keys=[purchase_order_id],
    )
    invoice = relationship(
        "Document",
        foreign_keys=[invoice_id],
    )
    delivery_note = relationship(
        "Document",
        foreign_keys=[delivery_note_id],
    )

    __table_args__ = (
        Index("ix_match_results_status", "status"),
        Index("ix_match_results_type_status", "match_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<MatchResult {self.id}:{self.status.value}>"

    def to_dict(self) -> dict:
        """Convert match result to dictionary."""
        return {
            "id": str(self.id),
            "match_type": self.match_type.value,
            "status": self.status.value,
            "total_score": self.total_score,
            "line_level_score": self.line_level_score,
            "amount_score": self.amount_score,
            "date_score": self.date_score,
            "po_amount": str(self.po_amount) if self.po_amount else None,
            "invoice_amount": str(self.invoice_amount) if self.invoice_amount else None,
            "delivery_amount": str(self.delivery_amount) if self.delivery_amount else None,
            "variance_amount": str(self.variance_amount),
            "total_line_items": self.total_line_items,
            "matched_line_items": self.matched_line_items,
            "partial_line_items": self.partial_line_items,
            "unmatched_line_items": self.unmatched_line_items,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MatchLineItem(Base):
    """Line item matching details."""

    __tablename__ = "match_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line item references
    po_line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_line_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_line_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_line_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Match status
    is_matched: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    match_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Quantities
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    invoice_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    delivery_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Amounts
    po_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    invoice_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    delivery_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    match_result = relationship("MatchResult", back_populates="line_items")

    def __repr__(self) -> str:
        return f"<MatchLineItem {self.id}>"

    def to_dict(self) -> dict:
        """Convert match line item to dictionary."""
        return {
            "id": str(self.id),
            "match_result_id": str(self.match_result_id),
            "is_matched": self.is_matched,
            "match_percentage": self.match_percentage,
            "quantity_variance": str(self.quantity_variance),
            "amount_variance": str(self.amount_variance),
        }


class ConfirmationRecord(Base):
    """Human confirmation records for learning loop."""

    __tablename__ = "confirmation_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Confirmation details
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    confirmed_action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(
        nullable=True,
    )
    feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    # Learning metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    match_result = relationship("MatchResult", back_populates="confirmations")

    def __repr__(self) -> str:
        return f"<ConfirmationRecord {self.id}>"
