// src/app/models/match.py
"""Match, MatchLine, MatchDecision, and CrossReference models."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Text, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.base import BaseModel


class MatchStatus(str, enum.Enum):
    """Match status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class MatchDecision(str, enum.Enum):
    """Match decision enumeration."""
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"
    PARTIAL_MATCH = "partial_match"


class Match(BaseModel):
    """
    Match model representing a 3-way match between Invoice, Delivery Note, and Purchase Order.
    This is the core entity of the 3-way matching engine.
    """
    
    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_invoice_id", "invoice_id"),
        Index("ix_matches_delivery_note_id", "delivery_note_id"),
        Index("ix_matches_purchase_order_id", "purchase_order_id"),
        Index("ix_matches_status", "status"),
        Index("ix_matches_decision", "decision"),
    )
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
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
    
    # Match scores
    line_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    
    amount_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    
    date_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    
    # Matched amounts
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    dn_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Variance reasons
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    date_variance_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    invoice = relationship("Invoice", back_populates="match")
    delivery_note = relationship(
        "DeliveryNote",
        back_populates="match",
        foreign_keys=[delivery_note_id],
    )
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="invoice_matches",
        foreign_keys=[purchase_order_id],
    )
    lines = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    cross_references = relationship(
        "CrossReference",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.id} - {self.match_type}>"


class MatchLine(BaseModel):
    """Line-level match details."""
    
    __tablename__ = "match_lines"
    __table_args__ = (
        Index("ix_match_lines_match_id", "match_id"),
    )
    
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    
    quantity_matched: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    quantity_invoice: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    quantity_po: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    quantity_dn: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    amount_matched: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    amount_invoice: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    amount_po: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    amount_dn: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Relationships
    match = relationship("Match", back_populates="lines")
    
    def __repr__(self) -> str:
        return f"<MatchLine {self.match_id}:{self.id}>"


class CrossReference(BaseModel):
    """
    Cross-reference table for human confirmations that feed back into future matching.
    This creates a learning loop for the matching engine.
    """
    
    __tablename__ = "cross_references"
    __table_args__ = (
        Index("ix_cross_references_supplier_item", "supplier_id", "item_code"),
        Index("ix_cross_references_match_id", "match_id"),
    )
    
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    po_item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    invoice_item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    dn_item_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    confirmed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    confirmation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    match = relationship("Match", back_populates="cross_references")
    
    def __repr__(self) -> str:
        return f"<CrossReference {self.po_item_code} -> {self.invoice_item_code}>"
