// src/models/match.py
"""Match and Match Line models for 3-way matching."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.user import User


class MatchStatus(str, Enum):
    """Match status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    AUTO_APPROVED = "auto_approved"
    PENDING_HUMAN_REVIEW = "pending_human_review"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class MatchType(str, Enum):
    """Match type enumeration."""

    PO_INVOICE = "po_invoice"
    PO_DELIVERY_NOTE = "po_delivery_note"
    INVOICE_DELIVERY_NOTE = "invoice_delivery_note"
    THREE_WAY = "three_way"


class Match(BaseModel):
    """Match model representing matched documents."""

    __tablename__ = "matches"

    match_type: Mapped[MatchType] = mapped_column(
        SQLEnum(MatchType, name="match_type"),
        nullable=False,
    )
    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status"),
        default=MatchStatus.PENDING,
        nullable=False,
    )

    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Match scores
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    date_score: Mapped[Decimal] = mapped_column(
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
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    delivery_note_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Variance details
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Decision routing
    decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    decision_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Review info
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
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
        back_populates="matched_invoices",
        lazy="selectin",
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="matches",
        lazy="selectin",
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
        back_populates="matches",
        lazy="selectin",
    )
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="selectin",
    )
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_match_status", "status"),
        Index("ix_match_type", "match_type"),
        Index("ix_match_overall_score", "overall_score"),
        Index("ix_match_po_id", "purchase_order_id"),
        Index("ix_match_invoice_id", "invoice_id"),
        Index("ix_match_dn_id", "delivery_note_id"),
    )

    def __repr__(self) -> str:
        return f"<Match type={self.match_type} status={self.status} score={self.overall_score}>"

    @property
    def decision_route(self) -> str:
        """Determine decision route based on overall score."""
        from src.app.config import get_settings
        settings = get_settings()

        if self.overall_score >= settings.MATCHING_AUTO_APPROVE_THRESHOLD:
            return "AUTO_APPROVE"
        elif self.overall_score >= settings.MATCHING_HUMAN_REVIEW_THRESHOLD:
            return "HUMAN_REVIEW"
        else:
            return "DISPUTE"


class MatchLine(BaseModel):
    """Match Line model for line-level matching details."""

    __tablename__ = "match_lines"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    # SKU matching
    sku_matched: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    sku_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    sku_target: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantity matching
    quantity_source: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    quantity_target: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    quantity_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Price matching
    price_source: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    price_target: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    price_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Amount matching
    amount_source: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    amount_target: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    amount_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Line-level match status
    is_matched: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    match_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_ml_match_id_line", "match_id", "line_number"),
    )

    def __repr__(self) -> str:
        return f"<MatchLine match_id={self.match_id} line={self.line_number}>"


import uuid
