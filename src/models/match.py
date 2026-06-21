// src/models/match.py
"""Match models for 3-way matching results."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.user import User


class Match(BaseModel):
    """3-Way Match record linking Invoice, Delivery Note, and Purchase Order."""

    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_invoice_id", "invoice_id"),
        Index("ix_matches_delivery_note_id", "delivery_note_id"),
        Index("ix_matches_purchase_order_id", "purchase_order_id"),
        Index("ix_matches_status", "status"),
        Index("ix_matches_decision", "decision"),
    )

    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Matching scores (0-100)
    line_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )  # Weighted 70%
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )  # Weighted 20%
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )  # Weighted 10%
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Matched amounts
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    po_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Decision
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, confirmed, rejected
    decision: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )  # CONFIRMED, PENDING, REJECTED, AUTO_APPROVED, HUMAN_REVIEW, DISPUTE

    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # full, partial, line_level

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Confirmation
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(back_populates="matches")
    delivery_note: Mapped["DeliveryNote | None"] = relationship(back_populates="matches")
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(back_populates="matches")
    confirmed_by_user: Mapped["User | None"] = relationship(
        back_populates="match_confirmations",
        foreign_keys=[confirmed_by],
    )
    lines: Mapped[list["MatchLine"]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    confirmations: Mapped[list["MatchConfirmation"]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )

    @property
    def confidence_level(self) -> str:
        """Get confidence level based on total score."""
        if self.total_score >= 95:
            return "high"
        elif self.total_score >= 80:
            return "medium"
        else:
            return "low"

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, decision={self.decision}, score={self.total_score})>"


class MatchLine(BaseModel):
    """Line-level matching details."""

    __tablename__ = "match_lines"
    __table_args__ = (
        Index("ix_match_lines_match_id", "match_id"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Matching details
    sku_match: Mapped[bool] = mapped_column(default=False, nullable=False)
    quantity_match: Mapped[bool] = mapped_column(default=False, nullable=False)
    price_match: Mapped[bool] = mapped_column(default=False, nullable=False)

    po_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    invoice_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    delivery_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)

    po_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    invoice_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    match: Mapped["Match"] = relationship(back_populates="lines")

    def __repr__(self) -> str:
        return f"<MatchLine(id={self.id}, matched_qty={self.matched_quantity})>"


class MatchConfirmation(BaseModel):
    """Human confirmation records for matches requiring review."""

    __tablename__ = "match_confirmations"
    __table_args__ = (
        Index("ix_match_confirmations_match_id", "match_id"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(String(30), nullable=False)  # approved, rejected
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    match: Mapped["Match"] = relationship(back_populates="confirmations")
    confirmed_by_user: Mapped["User"] = relationship(
        back_populates="match_confirmations",
        foreign_keys=[confirmed_by],
    )

    def __repr__(self) -> str:
        return f"<MatchConfirmation(id={self.id}, decision={self.decision})>"
