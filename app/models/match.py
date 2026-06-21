// app/models/match.py
"""Match models for 3-way matching results."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote
    from app.models.user import User


class MatchStatus(str):
    """Match status enumeration."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class MatchDecision(str):
    """Match decision enumeration."""
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


class MatchType(str):
    """Match type enumeration."""
    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY = "PO_DELIVERY"
    INVOICE_DELIVERY = "INVOICE_DELIVERY"
    THREE_WAY = "THREE_WAY"


class Match(Base):
    """Match model for 3-way matching results."""
    
    __tablename__ = "matches"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Match identification
    match_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
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
    
    # Match type
    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    # Scoring
    total_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    line_level_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    amount_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    date_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Status and decision
    status: Mapped[str] = mapped_column(
        String(20),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    decision: Mapped[str] = mapped_column(
        String(20),
        default=MatchDecision.HUMAN_REVIEW,
        nullable=False,
    )
    
    # Variance tracking
    quantity_variance: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    amount_variance: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    variance_threshold: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Human review
    confirmed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    confirmation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Dispute handling
    dispute_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    dispute_resolution: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    match_confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    source_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matches",
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="matches",
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matches",
    )
    
    confirmed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="match_confirmations",
        foreign_keys=[confirmed_by_user_id],
    )
    
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.match_number}>"
    
    def to_dict(self, include_lines: bool = False) -> dict:
        """Convert match to dictionary."""
        result = {
            "id": str(self.id),
            "match_number": self.match_number,
            "purchase_order_id": str(self.purchase_order_id) if self.purchase_order_id else None,
            "invoice_id": str(self.invoice_id) if self.invoice_id else None,
            "delivery_note_id": str(self.delivery_note_id) if self.delivery_note_id else None,
            "match_type": self.match_type,
            "total_score": self.total_score,
            "line_level_score": self.line_level_score,
            "amount_score": self.amount_score,
            "date_score": self.date_score,
            "status": self.status,
            "decision": self.decision,
            "quantity_variance": self.quantity_variance,
            "amount_variance": self.amount_variance,
            "variance_threshold": self.variance_threshold,
            "confirmed_by_user_id": str(self.confirmed_by_user_id) if self.confirmed_by_user_id else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "confirmation_notes": self.confirmation_notes,
            "dispute_reason": self.dispute_reason,
            "dispute_resolution": self.dispute_resolution,
            "match_confidence": self.match_confidence,
            "notes": self.notes,
            "source_system": self.source_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_lines:
            result["lines"] = [line.to_dict() for line in self.lines]
        
        return result


class MatchLine(Base):
    """Match Line Item for detailed line-level matching."""
    
    __tablename__ = "match_lines"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
    # Line references
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    delivery_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    # Product information
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    # Quantities
    po_quantity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    invoice_quantity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    delivery_quantity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    matched_quantity: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Amounts
    po_amount: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    invoice_amount: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    matched_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Scoring
    match_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Variance
    quantity_variance: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    amount_variance: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Match status
    is_matched: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    match_status: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<MatchLine {self.line_number}: {self.description[:30]}>"
    
    def to_dict(self) -> dict:
        """Convert match line to dictionary."""
        return {
            "id": str(self.id),
            "match_id": str(self.match_id),
            "po_line_id": str(self.po_line_id) if self.po_line_id else None,
            "invoice_line_id": str(self.invoice_line_id) if self.invoice_line_id else None,
            "delivery_line_id": str(self.delivery_line_id) if self.delivery_line_id else None,
            "line_number": self.line_number,
            "sku": self.sku,
            "description": self.description,
            "po_quantity": self.po_quantity,
            "invoice_quantity": self.invoice_quantity,
            "delivery_quantity": self.delivery_quantity,
            "matched_quantity": self.matched_quantity,
            "po_amount": self.po_amount,
            "invoice_amount": self.invoice_amount,
            "matched_amount": self.matched_amount,
            "match_score": self.match_score,
            "quantity_variance": self.quantity_variance,
            "amount_variance": self.amount_variance,
            "is_matched": self.is_matched,
            "match_status": self.match_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
