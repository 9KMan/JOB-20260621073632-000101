// src/app/models/match.py
"""Match Record models for 3-way matching."""
import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel


class MatchStatus(str, Enum):
    """Match status enumeration."""
    
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"


class MatchType(str, Enum):
    """Match type enumeration."""
    
    PO_INVOICE = "po_invoice"
    PO_DN = "po_dn"
    INVOICE_DN = "invoice_dn"
    THREE_WAY = "three_way"


class DecisionResult(str, Enum):
    """Decision routing result."""
    
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class MatchRecord(BaseModel):
    """Match Record for 3-way matching results."""
    
    __tablename__ = "match_records"
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    match_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    overall_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    line_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    amount_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    date_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    
    quantity_variance: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    amount_variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default=MatchStatus.PENDING.value, nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    
    variance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # noqa: F821
    
    match_details_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    invoice: Mapped[Optional["Invoice"]] = relationship(  # noqa: F821
        "Invoice",
        back_populates="match_records",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(  # noqa: F821
        "DeliveryNote",
        back_populates="match_records",
        foreign_keys=[delivery_note_id],
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(  # noqa: F821
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
    )
    reviewed_by_user: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User",
        back_populates="match_records",
        foreign_keys=[reviewed_by],
    )
    
    def __repr__(self) -> str:
        return f"<MatchRecord(id={self.id}, type={self.match_type}, status={self.status})>"


from datetime import datetime
from sqlalchemy import DateTime
