// src/app/models/match.py
"""Match model for 3-way matching results."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote
    from app.models.purchase_order import PurchaseOrder
    from app.models.user import User


class Match(BaseModel):
    """Match record for 3-way matching results."""

    __tablename__ = "matches"

    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Match type: INVOICE_PO, INVOICE_DN, DN_PO, THREE_WAY
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Decision status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
    )

    # Decision type: AUTO_APPROVE, HUMAN_REVIEW, DISPUTE
    decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Match scores
    line_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Amount comparisons
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    dn_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Notes and resolution
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="matches",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="matches",
        foreign_keys=[delivery_note_id],
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="matches",
        foreign_keys=[purchase_order_id],
    )
    resolved_by: Mapped["User"] = relationship(
        "User",
        back_populates="match_confirmations",
        foreign_keys=[resolved_by_id],
    )
    line_matches: Mapped[list["MatchLineDetail"]] = relationship(
        "MatchLineDetail",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    confirmations: Mapped[list["MatchConfirmation"]] = relationship(
        "MatchConfirmation",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_matches_status_decision", "status", "decision"),
        Index("ix_matches_invoice_po", "invoice_id", "purchase_order_id"),
    )

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, status={self.status}, total_score={self.total_score})>"


class MatchLineDetail(BaseModel):
    """Detailed line-level match information."""

    __tablename__ = "match_line_details"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line references
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match details
    line_match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SKU_MATCH",
    )
    quantity_match: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )
    amount_match: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="line_matches")

    def __repr__(self) -> str:
        return f"<MatchLineDetail(id={self.id}, match_score={self.match_score})>"


class MatchConfirmation(BaseModel):
    """Human confirmation/override for matches."""

    __tablename__ = "match_confirmations"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Original vs confirmed
    original_decision: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmed_decision: Mapped[str] = mapped_column(String(50), nullable=False)
    original_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Override details
    override_reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_approval: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="confirmations",
    )
    confirmed_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="match_confirmations",
    )

    def __repr__(self) -> str:
        return f"<MatchConfirmation(id={self.id}, decision={self.confirmed_decision})>"
