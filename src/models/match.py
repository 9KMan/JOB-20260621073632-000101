// src/models/match.py
"""Match models for 3-way matching."""
import decimal
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel


class MatchStatus(str, Enum):
    """Match status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    REJECTED = "rejected"


class MatchDecision(str, Enum):
    """Match decision enum."""
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class Match(BaseModel):
    """Match record for 3-way matching."""

    __tablename__ = "matches"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=MatchStatus.PENDING.value,
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(
        String(20),
        default=MatchDecision.HUMAN_REVIEW.value,
        nullable=False,
    )
    match_type: Mapped[str] = mapped_column(String(30), nullable=False)
    line_level_score: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    amount_score: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    date_score: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    total_score: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    invoice_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    po_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    dn_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    variance_percentage: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_variance_within_tolerance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    variance_tolerance_percentage: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2),
        default=5.00,
        nullable=False,
    )
    line_matches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    line_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="matches",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matches",
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matches",
    )
    match_lines: Mapped[List["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_matches_invoice_status", "invoice_id", "status"),
        Index("ix_matches_po_status", "purchase_order_id", "status"),
        Index("ix_matches_decision", "decision", "status"),
    )


class MatchLine(BaseModel):
    """Match line item for line-level matching details."""

    __tablename__ = "match_lines"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    po_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    invoice_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    dn_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    quantity_variance: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    variance_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    match_confidence: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="match_lines",
    )

    __table_args__ = (
        Index("ix_match_lines_match_id", "match_id"),
    )
