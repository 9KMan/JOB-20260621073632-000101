# src/app/models/matching.py
"""Matching models for 3-way matching."""
import decimal
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from src.app.models.enums import MatchStatus, MatchResultType, DecisionType

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.app.models.invoice import Invoice, InvoiceLine
    from src.app.models.delivery_note import DeliveryNote, DeliveryNoteLine
    from src.app.models.user import User


class MatchResult(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Result of matching between documents."""
    
    __tablename__ = "match_results"
    __table_args__ = (
        {"schema": "matching"},
    )
    
    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Match scores
    line_level_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    amount_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    date_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    total_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    
    # Match type
    match_type: Mapped[MatchResultType] = mapped_column(
        SQLEnum(MatchResultType, name="match_result_type", create_type=False),
        nullable=False,
    )
    
    # Match status
    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status", create_type=False),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Amount differences
    invoice_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    po_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    amount_difference: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    variance_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="match_results",
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="match_results",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
    )
    cross_references: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        back_populates="match_result",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    decisions: Mapped[list["MatchDecision"]] = relationship(
        "MatchDecision",
        back_populates="match_result",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<MatchResult(id={self.id}, status={self.status})>"


class CrossReference(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Cross-reference between matched lines from different documents."""
    
    __tablename__ = "cross_references"
    __table_args__ = (
        {"schema": "matching"},
    )
    
    # Match result reference
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matching.match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line references (at least one pair must be present)
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Match details
    quantity_matched: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        nullable=False,
    )
    amount_matched: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    match_confidence: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    
    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="cross_references",
    )
    invoice_line: Mapped[Optional["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="cross_references",
    )
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_invoice_lines",
    )
    dn_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="cross_references",
    )
    
    def __repr__(self) -> str:
        return f"<CrossReference(id={self.id})>"


class MatchDecision(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Human review decision on a match result."""
    
    __tablename__ = "match_decisions"
    __table_args__ = (
        {"schema": "matching"},
    )
    
    # Match result reference
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matching.match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Reviewer
    reviewed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Decision
    decision: Mapped[DecisionType] = mapped_column(
        SQLEnum(DecisionType, name="decision_type", create_type=False),
        nullable=False,
    )
    
    # Comments
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Previous and new status
    previous_status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status", create_type=False),
        nullable=False,
    )
    new_status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status", create_type=False),
        nullable=False,
    )
    
    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="decisions",
    )
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="decisions",
    )
    
    def __repr__(self) -> str:
        return f"<MatchDecision(id={self.id}, decision={self.decision})>"
