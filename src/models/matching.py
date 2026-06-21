// src/models/matching.py
"""Matching and Balance models for 3-way matching engine."""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from src.models.base import BaseModel
from src.models.enums import (
    MatchStatus, MatchType, BalanceType,
    match_status_enum, match_type_enum, balance_type_enum
)

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.user import User


class Match(BaseModel):
    """
    Match record linking documents together.
    
    Represents a confirmed or pending match between documents.
    """
    
    __tablename__ = "matches"
    
    # Document references
    po_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    invoice_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    dn_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Match metadata
    match_type: Mapped[MatchType] = mapped_column(
        match_type_enum,
        nullable=False,
        index=True
    )
    
    status: Mapped[MatchStatus] = mapped_column(
        match_status_enum,
        default=MatchStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Scoring
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Amount matching
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    dn_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    # Variance reasons
    variance_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Human review
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    confirmed_by_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    rejected_by_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
        foreign_keys=[po_id]
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_delivery_notes",
        foreign_keys=[invoice_id]
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matched_invoices",
        foreign_keys=[dn_id]
    )
    
    confirmed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="confirmed_matches",
        foreign_keys=[confirmed_by_id]
    )
    
    rejected_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="rejected_matches",
        foreign_keys=[rejected_by_id]
    )
    
    match_scores: Mapped[List["MatchScore"]] = relationship(
        "MatchScore",
        back_populates="match",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("po_id", "invoice_id", name="uq_match_po_invoice"),
        UniqueConstraint("po_id", "dn_id", name="uq_match_po_dn"),
        UniqueConstraint("invoice_id", "dn_id", name="uq_match_invoice_dn"),
        Index("ix_matches_status_type", "status", "match_type"),
        Index("ix_matches_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Match(id={self.id}, type={self.match_type}, status={self.status})>"


class MatchScore(BaseModel):
    """
    Detailed scoring for each line item in a match.
    
    Stores granular scores for product code matching,
    quantity matching, and price matching at line level.
    """
    
    __tablename__ = "match_scores"
    
    match_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Line identifiers
    po_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    
    invoice_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    
    dn_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Product matching
    product_code_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    product_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Quantity matching
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    
    invoice_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    
    dn_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    
    quantity_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Price matching
    po_unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    invoice_unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    price_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Amount matching
    po_line_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    invoice_line_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    dn_line_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    line_amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    # Combined line score
    line_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="match_scores"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_match_scores_match_id", "match_id"),
    )
    
    def __repr__(self) -> str:
        return f"<MatchScore(id={self.id}, line_score={self.line_score})>"


class BalanceEntry(BaseModel):
    """
    Balance ledger for tracking partial matches.
    
    Tracks remaining balances across invoices, delivery notes,
    and purchase orders for partial shipment and split invoice scenarios.
    """
    
    __tablename__ = "balance_entries"
    
    # Document references
    po_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    invoice_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    dn_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(
        balance_type_enum,
        nullable=False,
        index=True
    )
    
    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Match reference
    match_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Line reference (optional)
    po_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    
    invoice_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    
    dn_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Status
    is_settled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    settled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries",
        foreign_keys=[po_id]
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balance_entries",
        foreign_keys=[invoice_id]
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balance_entries",
        foreign_keys=[dn_id]
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_balance_entries_document", "invoice_id", "dn_id", "po_id"),
        Index("ix_balance_entries_type_status", "balance_type", "is_settled"),
    )
    
    def __repr__(self) -> str:
        return f"<BalanceEntry(id={self.id}, type={self.balance_type}, remaining={self.remaining_amount})>"
