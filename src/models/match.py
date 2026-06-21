// src/models/match.py
"""Match and Match Line Detail models."""
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.purchase_order import PurchaseOrder
    from src.models.user import User


class MatchLineDetail(BaseModel):
    """Match Line Detail - individual line matching results."""
    
    __tablename__ = "match_line_details"
    
    match_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    purchase_order_line_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    quantity_match: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=True,
    )
    quantity_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=True,
    )
    amount_match: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    amount_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    line_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="line_details",
    )
    
    def __repr__(self) -> str:
        return f"<MatchLineDetail {self.id}>"


class Match(BaseModel):
    """Match model - 3-way matching results between Invoice, DN, and PO."""
    
    __tablename__ = "matches"
    
    invoice_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    match_type: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
    )
    match_status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        default="PENDING",
        index=True,
    )
    line_level_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    amount_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    date_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
    )
    variance_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    variance_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    decision: Mapped[Optional[str]] = mapped_column(
        String(length=30),
        nullable=True,
        index=True,
    )
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="matches",
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matches",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matches",
    )
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by],
    )
    line_details: Mapped[List["MatchLineDetail"]] = relationship(
        "MatchLineDetail",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.id}: {self.overall_score}%>"
