// app/models/matching.py
"""Matching and Balance Ledger models."""
import uuid
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote
    from app.models.user import User


class MatchResult(Base, UUIDMixin, TimestampMixin):
    """Result of 3-way matching process."""
    
    __tablename__ = "match_results"
    
    # Document references
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
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Match scores
    line_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    amount_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    date_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
    )
    
    # Match status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="HUMAN_REVIEW",
    )
    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="HUMAN_REVIEW",
    )
    
    # Match details
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    variance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_match_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="match_results",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="match_results",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="match_results",
    )
    confirmation: Mapped["MatchConfirmation | None"] = relationship(
        "MatchConfirmation",
        back_populates="match_result",
        uselist=False,
    )
    
    def __repr__(self) -> str:
        return f"<MatchResult {self.id} status={self.status}>"


class MatchConfirmation(Base, UUIDMixin, TimestampMixin):
    """Human confirmation of match result."""
    
    __tablename__ = "match_confirmations"
    
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    confirmed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Confirmation details
    confirmed: Mapped[bool] = mapped_column(nullable=False)
    final_status: Mapped[str] = mapped_column(String(20), nullable=False)
    final_action: Mapped[str] = mapped_column(String(30), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        "MatchResult",
        back_populates="confirmation",
    )
    confirmed_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="confirmations",
    )
    
    def __repr__(self) -> str:
        return f"<MatchConfirmation {self.id} confirmed={self.confirmed}>"


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Tracks balances for partial matches across documents."""
    
    __tablename__ = "balance_ledger"
    
    # Document references
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
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Balance tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Line-level tracking
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
    )
    remaining_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    
    # Status
    is_settled: Mapped[bool] = mapped_column(default=False, nullable=False)
    settlement_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="balance_ledger_entries",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger {self.id} remaining={self.remaining_amount}>"
