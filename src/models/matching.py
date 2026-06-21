// src/models/matching.py
"""Matching models for 3-way matching engine."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote
    from app.models.purchase_order import PurchaseOrder
    from app.models.user import User


class Match(Base, BaseModel):
    """Match record for 3-way matching."""

    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_match_invoice_id", "invoice_id"),
        Index("ix_match_delivery_note_id", "delivery_note_id"),
        Index("ix_match_po_id", "purchase_order_id"),
        Index("ix_match_status_decision", "status", "decision"),
    )

    # Document references
    invoice_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    delivery_note_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    purchase_order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Match scores
    line_level_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    amount_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    date_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    # Match status
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # PENDING, CONFIRMED, REJECTED
    decision: Mapped[str] = mapped_column(String(30), default="HUMAN_REVIEW", nullable=False)  # AUTO_APPROVE, HUMAN_REVIEW, DISPUTE
    decision_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Amount comparisons
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    po_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)

    # Review info
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    invoice: Mapped["Invoice"] = relationship("Invoice", foreign_keys=[invoice_id])
    delivery_note: Mapped["DeliveryNote"] = relationship("DeliveryNote", foreign_keys=[delivery_note_id])
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    reviewed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<Match {self.id} - Score: {self.total_score}>"


class MatchLine(Base, BaseModel):
    """Individual line matches within a match record."""

    __tablename__ = "match_lines"
    __table_args__ = (
        Index("ix_ml_match_id_line_number", "match_id", "line_number", unique=True),
    )

    match_id: Mapped[str] = mapped_column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Line references
    invoice_line_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    delivery_note_line_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    purchase_order_line_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Line comparisons
    item_code_match: Mapped[bool] = mapped_column(default=False, nullable=False)
    item_description_match: Mapped[bool] = mapped_column(default=False, nullable=False)
    quantity_match: Mapped[bool] = mapped_column(default=False, nullable=False)
    price_match: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Quantities
    invoice_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    delivery_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)

    # Prices
    invoice_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    delivery_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    po_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)

    # Line scores
    quantity_variance: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    price_variance: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    line_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    # Match status for this line
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # MATCHED, VARIANCE, UNMATCHED

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="lines")

    def __repr__(self) -> str:
        return f"<MatchLine {self.line_number}>"


class MatchDecision(Base, BaseModel):
    """Historical record of human match decisions for learning loop."""

    __tablename__ = "match_decisions"
    __table_args__ = (
        Index("ix_md_user_id_decision_date", "reviewed_by", "created_at"),
    )

    match_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    previous_decision: Mapped[str] = mapped_column(String(30), nullable=False)
    new_decision: Mapped[str] = mapped_column(String(30), nullable=False)
    reviewed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    reviewed_by_user: Mapped["User"] = relationship("User", back_populates="match_decisions")

    def __repr__(self) -> str:
        return f"<MatchDecision {self.id}>"
