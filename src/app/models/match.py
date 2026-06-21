// src/app/models/match.py
"""
Match Model
Stores 3-way matching results and decisions.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric, ForeignKey, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Match(BaseModel):
    """Match record for 3-way matching."""
    
    __tablename__ = "matches"
    
    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Match type and status
    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'invoice_po', 'invoice_dn', 'dn_po', 'three_way'
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # 'confirmed', 'pending', 'rejected'
    
    # Scoring
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
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    
    # Variance analysis
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Decision
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'AUTO_APPROVE', 'HUMAN_REVIEW', 'DISPUTE'
    
    # Decision details
    decision_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.id}: {self.match_type} - {self.decision}>"


class MatchConfirmation(BaseModel):
    """Human confirmation for matches requiring review."""
    
    __tablename__ = "match_confirmations"
    
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'confirmed', 'rejected', 'adjusted'
    
    # Adjustment details if applicable
    adjusted_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    adjusted_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    # Comments and notes
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="confirmations")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<MatchConfirmation {self.id}: {self.decision}>"
