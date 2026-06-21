// src/models/matching.py
"""Matching models for 3-way matching operations."""
import enum
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Index, Enum, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class MatchStatus(str, enum.Enum):
    """Match result status."""
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class MatchType(str, enum.Enum):
    """Type of line match."""
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    CLOSE = "CLOSE"
    NO_MATCH = "NO_MATCH"


class BalanceType(str, enum.Enum):
    """Balance type enumeration."""
    OVER = "OVER"
    UNDER = "UNDER"
    MATCHED = "MATCHED"


class BalanceStatus(str, enum.Enum):
    """Balance status enumeration."""
    BALANCED = "BALANCED"
    PARTIAL_BALANCE = "PARTIAL_BALANCE"
    UNBALANCED = "UNBALANCED"


class MatchResult(BaseModel):
    """Result of a 3-way matching operation."""
    __tablename__ = "match_results"

    invoice_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    delivery_note_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    purchase_order_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(MatchStatus),
        default=MatchStatus.PENDING_REVIEW,
        nullable=False,
        index=True
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    invoice_po_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    dn_po_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    invoice_dn_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    date_variance_days: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    balance_status: Mapped[str] = mapped_column(
        String(50),
        default=BalanceStatus.BALANCED.value,
        nullable=False
    )
    warnings: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True
    )
    match_details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # Relationships
    line_matches: Mapped[list["MatchResultLineMatch"]] = relationship(
        "MatchResultLineMatch",
        back_populates="match_result",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    cross_references: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        back_populates="match_result",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("ix_match_results_status_date", "status", "created_at"),
    )


class MatchResultLineMatch(BaseModel):
    """Line-level match details within a match result."""
    __tablename__ = "match_result_line_matches"

    match_result_id: Mapped[str] = mapped_column(
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    source_line_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    source_line_number: Mapped[int] = mapped_column(
        nullable=False
    )
    target_document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    target_line_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    target_line_number: Mapped[int] = mapped_column(
        nullable=False
    )
    match_type: Mapped[str] = mapped_column(
        Enum(MatchType),
        default=MatchType.NO_MATCH,
        nullable=False
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )

    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="line_matches"
    )


class CrossReference(BaseModel):
    """Cross-reference table for human confirmations that feed into matching."""
    __tablename__ = "cross_references"

    match_result_id: Mapped[str] = mapped_column(
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_document_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    source_document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    source_line_number: Mapped[int] = mapped_column(
        nullable=False
    )
    target_document_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    target_document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    target_line_number: Mapped[int] = mapped_column(
        nullable=False
    )
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False
    )
    confirmed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="cross_references"
    )

    __table_args__ = (
        Index("ix_cross_ref_source", "source_document_id", "source_document_type"),
        Index("ix_cross_ref_target", "target_document_id", "target_document_type"),
    )


class BalanceLedger(BaseModel):
    """Ledger for tracking balances across partial matches."""
    __tablename__ = "balance_ledger"

    document_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    reference_document_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    reference_document_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    balance_type: Mapped[str] = mapped_column(
        Enum(BalanceType),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="OPEN",
        nullable=False,
        index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    __table_args__ = (
        Index("ix_balance_ledger_doc_ref", "document_id", "reference_document_id"),
    )
