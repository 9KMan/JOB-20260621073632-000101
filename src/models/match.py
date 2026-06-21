// src/models/match.py
"""Match model for 3-way matching results."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from models.base import BaseModel


class MatchType(str, Enum):
    """Types of matches in the 3-way matching system."""
    
    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY = "PO_DELIVERY"
    INVOICE_DELIVERY = "INVOICE_DELIVERY"
    THREE_WAY = "THREE_WAY"


class MatchStatus(str, Enum):
    """Status of a match record."""
    
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


class MatchDecision(str, Enum):
    """Decision result from the decision engine."""
    
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


class Match(Base, BaseModel):
    """Match record capturing matching results between documents."""

    __tablename__ = "matches"

    # Match type and status
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=MatchStatus.PENDING.value, index=True)
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    
    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
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
    
    # Matching scores
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    line_level_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    amount_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    date_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    
    # Matched amounts
    po_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    invoice_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    delivery_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    
    # Matched quantities (JSON for line-level details)
    line_matching_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Variance reasons
    variance_reasons: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Decision notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
    )
    confirmations: Mapped[List["MatchConfirmation"]] = relationship(
        "MatchConfirmation",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Match {self.match_type} - Score: {self.total_score}>"


class MatchConfirmation(Base, BaseModel):
    """Confirmation records for match learning loop."""

    __tablename__ = "match_confirmations"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Document pair that was confirmed/rejected
    document_type_1: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id_1: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_type_2: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id_2: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    # Confirmation result
    is_confirmed: Mapped[bool] = mapped_column(nullable=False)
    confirmed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    confirmation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Learning data
    weight_adjustments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="confirmations",
    )

    def __repr__(self) -> str:
        return f"<MatchConfirmation {self.document_type_1}-{self.document_type_2}>"
