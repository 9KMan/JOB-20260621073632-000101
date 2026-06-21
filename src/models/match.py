// src/models/match.py
"""Match, MatchLine, and BalanceLedger models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import MatchStatus, MatchDecision, MatchType

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.models.invoice import Invoice, InvoiceLine
    from src.models.delivery_note import DeliveryNote, DeliveryNoteLine


class Match(BaseModel):
    """3-Way Match header capturing the complete match result."""

    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_match_invoice", "invoice_id"),
        Index("ix_match_status_decision", "status", "decision"),
        UniqueConstraint("invoice_id", name="uq_match_invoice"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[MatchStatus] = mapped_column(
        MatchStatus.enum,
        default=MatchStatus.PENDING,
        nullable=False,
    )
    decision: Mapped[MatchDecision] = mapped_column(
        MatchDecision.enum,
        default=MatchDecision.HUMAN_REVIEW,
        nullable=False,
    )
    match_type: Mapped[MatchType] = mapped_column(
        MatchType.enum,
        nullable=False,
    )
    overall_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    line_level_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    amount_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    date_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    invoice_total: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    po_total: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    delivery_total: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    variance_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    variance_reason: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    confirmed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejected_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="matched_lines",
        foreign_keys=[invoice_id],
    )
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    confirmed_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="confirmed_matches",
        foreign_keys=[confirmed_by_id],
    )
    rejected_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="rejected_matches",
        foreign_keys=[rejected_by_id],
    )

    def __repr__(self) -> str:
        return f"<Match {self.id}: {self.status.value} - {self.decision.value}>"


class MatchLine(BaseModel):
    """Individual line-level matches between PO, Invoice, and Delivery Note lines."""

    __tablename__ = "match_lines"
    __table_args__ = (
        Index("ix_ml_match_line", "match_id", "line_number", unique=True),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_type: Mapped[MatchType] = mapped_column(
        MatchType.enum,
        nullable=False,
    )
    score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    quantity_matched: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    quantity_variance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    amount_matched: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    amount_variance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    is_partial: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_lines",
        foreign_keys=[po_line_id],
    )
    invoice_line: Mapped["InvoiceLine"] = relationship(
        "InvoiceLine",
        back_populates="matched_lines",
        foreign_keys=[invoice_line_id],
    )
    delivery_note_line: Mapped["DeliveryNoteLine"] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_lines",
        foreign_keys=[delivery_line_id],
    )

    def __repr__(self) -> str:
        return f"<MatchLine {self.line_number}: Score {self.score}>"


class BalanceLedger(BaseModel):
    """Tracks running balances across PO, Invoice, and Delivery Note for partial match resolution."""

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_bl_po", "po_id"),
        Index("ix_bl_invoice", "invoice_id"),
        Index("ix_bl_delivery", "delivery_note_id"),
    )

    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    original_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    balance_remaining: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    original_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    quantity_remaining: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    is_settled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    settled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries",
        foreign_keys=[po_id],
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_entries",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="balance_entries",
        foreign_keys=[delivery_note_id],
    )
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}: {self.balance_remaining} remaining>"
