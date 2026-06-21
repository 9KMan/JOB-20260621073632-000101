// src/app/models/match.py
"""Match models for 3-way matching."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class MatchDecision(str, Enum):
    """Match decision outcomes."""
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


class MatchType(str, Enum):
    """Type of match performed."""
    INVOICE_PO = "INVOICE_PO"
    DN_PO = "DN_PO"
    INVOICE_DN = "INVOICE_DN"
    THREE_WAY = "THREE_WAY"


class Match(Base, UUIDMixin, TimestampMixin):
    """Match record between documents."""

    __tablename__ = "matches"

    # Document references
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Match metadata
    match_type: Mapped[MatchType] = mapped_column(
        SQLEnum(MatchType, name="match_type"),
        nullable=False,
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
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

    # Match amounts
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    dn_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    # Decision
    decision: Mapped[MatchDecision] = mapped_column(
        SQLEnum(MatchDecision, name="match_decision"),
        default=MatchDecision.HUMAN_REVIEW,
        nullable=False,
    )
    confirmed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispute_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(  # noqa: F821
        "PurchaseOrder",
        back_populates="matches",
        foreign_keys=[purchase_order_id],
    )
    invoice: Mapped["Invoice"] = relationship(  # noqa: F821
        "Invoice",
        back_populates="matches",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(  # noqa: F821
        "DeliveryNote",
        back_populates="matches",
        foreign_keys=[delivery_note_id],
    )
    confirmed_by_user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="matches_confirmed",
        foreign_keys=[confirmed_by_id],
    )
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            "purchase_order_id",
            "delivery_note_id",
            name="uq_match_documents",
        ),
        Index("ix_match_decision", "decision"),
        Index("ix_match_type", "match_type"),
        Index("ix_match_score", "match_score"),
    )


class MatchLine(Base, UUIDMixin, TimestampMixin):
    """Line-level match details."""

    __tablename__ = "match_lines"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Line match scores
    product_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    quantity_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    price_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    line_total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )

    # Quantities
    po_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    invoice_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    dn_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
    )

    # Amounts
    po_line_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    invoice_line_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    dn_line_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_ml_match_id", "match_id"),
    )


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance tracking for partial matches."""

    __tablename__ = "balance_ledger"

    # Document references
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PO, Invoice, DN
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_line_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Balance tracking
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Reference to match
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadata
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_bl_document", "document_type", "document_id"),
        Index("ix_bl_match_id", "match_id"),
    )


# Add reverse relationships
from app.models.purchase_order import PurchaseOrder
from app.models.invoice import Invoice
from app.models.delivery_note import DeliveryNote

PurchaseOrder.matches = relationship(
    "Match",
    back_populates="purchase_order",
    foreign_keys="Match.purchase_order_id",
)
Invoice.matches = relationship(
    "Match",
    back_populates="invoice",
    foreign_keys="Match.invoice_id",
)
DeliveryNote.matches = relationship(
    "Match",
    back_populates="delivery_note",
    foreign_keys="Match.delivery_note_id",
)
