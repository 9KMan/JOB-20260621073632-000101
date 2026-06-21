# src/models/match.py
import uuid
import decimal
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Numeric, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class MatchStatus(str, Enum):
    """Match status enumeration."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class MatchType(str, Enum):
    """Match type enumeration."""
    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY = "PO_DELIVERY"
    INVOICE_DELIVERY = "INVOICE_DELIVERY"
    THREE_WAY = "THREE_WAY"


class Match(Base, UUIDMixin, TimestampMixin):
    """Match model for 3-way matching results."""
    
    __tablename__ = "matches"
    
    # Match type
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Match status
    status: Mapped[str] = mapped_column(String(20), default=MatchStatus.PENDING.value, nullable=False, index=True)
    
    # Confidence score (0.0 to 1.0)
    confidence_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=decimal.Decimal("0.0")
    )
    
    # Component scores
    line_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=decimal.Decimal("0.0")
    )
    amount_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=decimal.Decimal("0.0")
    )
    date_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=decimal.Decimal("0.0")
    )
    
    # Document IDs
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
    
    # Amounts
    po_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    invoice_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    delivery_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    variance_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Review
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Decision
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    auto_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    delivery_note = relationship("DeliveryNote", foreign_keys=[delivery_note_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self) -> str:
        return f"<Match {self.id} - {self.match_type} - {self.status}>"
