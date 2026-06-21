// src/models/match.py
"""Match model for 3-way matching results."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.delivery_note import DeliveryNote
    from src.models.invoice import Invoice
    from src.models.purchase_order import PurchaseOrder


class MatchStatus(str, enum.Enum):
    """Match decision status."""
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


class MatchType(str, enum.Enum):
    """Type of match performed."""
    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY = "PO_DELIVERY"
    INVOICE_DELIVERY = "INVOICE_DELIVERY"
    THREE_WAY = "THREE_WAY"


class Match(BaseModel):
    """Match record for 3-way matching results."""

    __tablename__ = "matches"

    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType),
        nullable=False,
        index=True
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Match scores
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False
    )
    
    # Matched amounts
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    
    # Variance details
    quantity_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True
    )
    price_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True
    )
    date_variance_days: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )
    
    # Related documents
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Resolution
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Detailed line matching data
    line_matches: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=list
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matches"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="matches"
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matches"
    )

    def __repr__(self) -> str:
        return f"<Match {self.id}: {self.match_type.value} - {self.status.value}>"

    @property
    def is_confirmed(self) -> bool:
        """Check if match is confirmed."""
        return self.status in (MatchStatus.CONFIRMED, MatchStatus.AUTO_APPROVED)

    @property
    def needs_review(self) -> bool:
        """Check if match needs human review."""
        return self.status == MatchStatus.HUMAN_REVIEW

    def approve(self, resolved_by: Optional[uuid.UUID] = None, notes: Optional[str] = None) -> None:
        """Approve the match."""
        self.status = MatchStatus.CONFIRMED
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        if notes:
            self.resolution_notes = notes

    def reject(self, reason: str, resolved_by: Optional[uuid.UUID] = None) -> None:
        """Reject the match."""
        self.status = MatchStatus.REJECTED
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = reason


# Association table for Invoice-DeliveryNote many-to-many (additional to matches)
match_invoice_delivery_notes = Table(
    "match_invoice_delivery_notes",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("invoice_id", UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE")),
    Column("delivery_note_id", UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE")),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow),
    Column("is_deleted", Boolean, default=False, nullable=False)
)
