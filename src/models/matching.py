// src/models/matching.py
"""Matching models for 3-way matching engine."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class MatchRecord(BaseModel):
    """
    Match Record - Captures a match between documents in 3-way matching.
    
    Match Types:
    - PO_INVOICE: Match between Purchase Order and Invoice
    - PO_DELIVERY: Match between Purchase Order and Delivery Note
    - INVOICE_DELIVERY: Match between Invoice and Delivery Note
    - THREE_WAY: Complete match across all three documents
    
    Decisions:
    - PENDING: Awaiting decision
    - CONFIRMED: Match confirmed, auto-approved
    - REJECTED: Match rejected, flagged for dispute
    """
    
    __tablename__ = "match_records"
    
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )
    
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    
    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING"
    )
    
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="match_records"
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="match_records"
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="match_records"
    )
    
    decider: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="decided_matches",
        foreign_keys=[decided_by]
    )
    
    decision_history: Mapped[list["MatchDecision"]] = relationship(
        "MatchDecision",
        back_populates="match_record",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<MatchRecord {self.match_type}: {self.match_score}%>"


class MatchDecision(BaseModel):
    """History of decisions made on match records."""
    
    __tablename__ = "match_decisions"
    
    match_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    previous_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    new_decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    match_record: Mapped["MatchRecord"] = relationship(
        "MatchRecord",
        back_populates="decision_history"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="decision_history"
    )
    
    def __repr__(self) -> str:
        return f"<MatchDecision {self.previous_decision} -> {self.new_decision}>"
