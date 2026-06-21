// src/app/models/match.py
"""Match Result and Confirmation models."""
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.user import User


class MatchResult(BaseModel):
    """Result of matching between Invoice, Delivery Note, and PO."""

    __tablename__ = "match_results"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Matching scores (0.0 to 1.0)
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    
    # Match decision
    match_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )
    decision_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Match type
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="THREE_WAY",
    )
    
    # Detailed match data
    match_details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Variance tracking
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    
    # Routing
    routing_decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="HUMAN_REVIEW",
    )
    
    # Confirmation tracking
    is_confirmed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[date | None] = mapped_column(
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        back_populates="matches",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        back_populates="matches",
        foreign_keys=[delivery_note_id],
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        foreign_keys=[po_id],
    )
    confirmed_by_user: Mapped["User | None"] = relationship(
        back_populates="match_confirmations",
        foreign_keys=[confirmed_by],
    )
    confirmations: Mapped[list["MatchConfirmation"]] = relationship(
        back_populates="match_result",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MatchResult {self.id} - {self.match_status}>"


class MatchConfirmation(BaseModel):
    """Human confirmation records for match learning."""

    __tablename__ = "match_confirmations"

    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmation_action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    previous_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    adjusted_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        back_populates="confirmations",
    )
    confirmed_by_user: Mapped["User"] = relationship(
        back_populates="match_confirmations",
        foreign_keys=[confirmed_by],
    )

    def __repr__(self) -> str:
        return f"<MatchConfirmation {self.confirmation_action}>"
