// src/models/match.py
"""Match model for 3-way matching results."""
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base

if TYPE_CHECKING:
    from src.models.document import Document
    from src.models.user import User


class MatchStatus(str, Enum):
    """Status of a match."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Decision result of matching."""
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    DISPUTED = "disputed"


class MatchType(str, Enum):
    """Type of match relationship."""
    PO_INVOICE = "po_invoice"
    PO_DELIVERY = "po_delivery"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class Match(UUIDMixin, Base):
    """
    Match record representing a match between documents.
    Can be PO↔Invoice, PO↔Delivery, Invoice↔Delivery, or all three.
    """
    
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "target_document_id",
            "match_type",
            name="uq_source_target_match_type",
        ),
    )
    
    # Document references
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    third_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Match type
    match_type: Mapped[MatchType] = mapped_column(
        nullable=False,
    )
    
    # Scoring
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    line_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False,
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False,
    )
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Matched amounts
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Status and decision
    status: Mapped[MatchStatus] = mapped_column(
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    decision: Mapped[Optional[MatchDecision]] = mapped_column(
        nullable=True,
    )
    
    # Variance details
    variance_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tolerance_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Approval
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approval_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    source_document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[source_document_id],
    )
    target_document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[target_document_id],
    )
    third_document: Mapped[Optional["Document"]] = relationship(
        "Document",
        foreign_keys=[third_document_id],
    )
    approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_id],
    )
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.id}:{self.match_type.value}={self.total_score}>"


class MatchLine(UUIDMixin, Base):
    """Line-level matching details."""
    
    __tablename__ = "match_lines"
    __table_args__ = (
        UniqueConstraint(
            "match_id", "source_line_id", name="uq_match_source_line"
        ),
    )
    
    # Foreign keys
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Matched quantities
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    variance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Matched amounts
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Line-level score
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    # Status
    is_confirmed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    confirmed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<MatchLine {self.id}>"


import uuid
from datetime import datetime
from decimal import Decimal
