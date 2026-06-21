// src/models/matching.py
"""Matching and balance tracking models."""
import decimal
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.document import Document, DocumentLine


class MatchConfidence(str, enum.Enum):
    """Match confidence level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class MatchDecision(str, enum.Enum):
    """Match decision status."""

    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
    DISPUTED = "disputed"


class MatchResult(str, enum.Enum):
    """Overall match result."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    REJECTED = "rejected"


class MatchingRecord(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Record of a matching operation between documents.
    Tracks the matching score and decision.
    """

    __tablename__ = "matching_records"

    # Primary document being matched
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="matching_records",
        foreign_keys=[document_id],
    )

    # Matched document
    matched_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matched_document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[matched_document_id],
    )

    # Match type
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Scoring
    line_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )
    amount_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )
    date_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )
    overall_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )

    # Confidence
    confidence: Mapped[MatchConfidence] = mapped_column(
        Enum(MatchConfidence),
        default=MatchConfidence.NONE,
        nullable=False,
    )

    # Decision
    decision: Mapped[MatchDecision] = mapped_column(
        Enum(MatchDecision),
        default=MatchDecision.PENDING,
        nullable=False,
    )
    result: Mapped[MatchResult] = mapped_column(
        Enum(MatchResult),
        default=MatchResult.PENDING,
        nullable=False,
    )

    # Matched amounts
    matched_line_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    total_line_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )

    # Balance tracking
    balance_after_match: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )

    # Review information
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[date | None] = mapped_column(
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Confirmation for learning loop
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Matched line references
    matched_line_ids: Mapped[list[uuid.UUID]] = mapped_column(
        nullable=True,
    )

    __table_args__ = (
        Index("ix_matching_records_document", "document_id", "matched_document_id"),
        Index("ix_matching_records_decision", "decision", "result"),
    )

    def __repr__(self) -> str:
        return f"<MatchingRecord {self.id}: score={self.overall_score}>"


class BalanceRecord(Base, UUIDMixin, TimestampMixin):
    """
    Tracks balance amounts for partial matching scenarios.
    Enables split invoices, partial shipments, and multi-delivery matching.
    """

    __tablename__ = "balance_records"

    # Document this balance belongs to
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="balance_records",
    )

    # Related matching record
    matching_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matching_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Amounts
    original_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    remaining_balance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Status
    is_settled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    settled_at: Mapped[date | None] = mapped_column(
        nullable=True,
    )

    # Reference to settlement document
    settled_by_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_balance_records_document_settled", "document_id", "is_settled"),
    )

    def __repr__(self) -> str:
        return f"<BalanceRecord {self.id}: remaining={self.remaining_balance}>"


# Import date for reviewed_at field
from datetime import date
