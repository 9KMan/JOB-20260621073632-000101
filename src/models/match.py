// src/models/match.py
"""Match models."""
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TimestampMixin


class MatchType(str, Enum):
    """Match type enumeration."""
    INVOICE_PO = "invoice_po"
    DELIVERY_PO = "delivery_po"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class MatchStatus(str, Enum):
    """Match status."""
    PENDING = "pending"
    AUTO_CONFIRMED = "auto_confirmed"
    HUMAN_REVIEW = "human_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class MatchResult(str, Enum):
    """Match result."""
    EXACT = "exact"
    PARTIAL = "partial"
    OVER = "over"
    UNDER = "under"
    NO_MATCH = "no_match"


class MatchRecord(BaseModel, TimestampMixin):
    """Match record between documents."""
    
    __tablename__ = "match_records"
    
    match_type: Mapped[MatchType] = mapped_column(
        SQLEnum(MatchType, name="match_type", create_type=False),
        nullable=False,
    )
    
    invoice_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    purchase_order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    line_match_details: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    quantity_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    amount_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    date_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    match_result: Mapped[MatchResult] = mapped_column(
        SQLEnum(MatchResult, name="match_result", create_type=False),
        nullable=False,
    )
    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status", create_type=False),
        default=MatchStatus.PENDING,
        nullable=False,
    )
    
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    variance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    invoice: Mapped["Invoice"] = relationship(foreign_keys=[invoice_id])
    purchase_order: Mapped["PurchaseOrder"] = relationship(foreign_keys=[purchase_order_id])
    delivery_note: Mapped["DeliveryNote"] = relationship(foreign_keys=[delivery_note_id])
    confirmations: Mapped[list["MatchConfirmation"]] = relationship(
        back_populates="match_record",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<MatchRecord {self.id}: {self.match_type} - {self.status}>"


class MatchConfirmation(BaseModel, TimestampMixin):
    """Match confirmation from human review."""
    
    __tablename__ = "match_confirmations"
    
    match_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    decision: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status_confirm", create_type=False),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    match_record: Mapped["MatchRecord"] = relationship(
        back_populates="confirmations",
    )
    
    def __repr__(self) -> str:
        return f"<MatchConfirmation {self.id}: {self.decision}>"
