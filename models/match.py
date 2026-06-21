// models/match.py
"""Match model for 3-way matching results."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNote, DeliveryNoteLine
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import PurchaseOrder


class MatchStatus(str, Enum):
    """Match status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    PARTIAL = "partial"


class MatchDecision(str, Enum):
    """Match decision enumeration."""
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"
    PARTIALLY_MATCHED = "partially_matched"


class Match(BaseModel):
    """
    Match model representing a 3-way match between Invoice, Delivery Note, and Purchase Order.
    
    This is the core entity that tracks the matching process and decision outcomes.
    """
    
    __tablename__ = "matches"
    
    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Match metrics
    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # full_3way, invoice_po, invoice_dn, partial
    
    overall_confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )  # 0.0000 to 1.0000
    
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    
    # Amount comparison
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    dn_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    variance_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Status and decision
    status: Mapped[str] = mapped_column(
        String(20),
        default=MatchStatus.PENDING.value,
        nullable=False,
    )
    
    decision: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    
    # Timestamps
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Additional info
    is_auto_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[Optional[dict]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON data
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="matches",
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matches",
    )
    
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="matches",
    )
    
    lines: Mapped[List["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.id} - {self.match_type}>"
    
    @property
    def is_confirmed(self) -> bool:
        """Check if match is confirmed."""
        return self.status == MatchStatus.CONFIRMED.value
    
    @property
    def is_pending(self) -> bool:
        """Check if match is pending review."""
        return self.status == MatchStatus.PENDING.value
    
    @property
    def is_rejected(self) -> bool:
        """Check if match is rejected."""
        return self.status == MatchStatus.REJECTED.value


class MatchLine(BaseModel):
    """Line-level match details within a Match."""
    
    __tablename__ = "match_lines"
    
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Line references
    invoice_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Line-level matching
    line_confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    quantity_matched: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    
    quantity_invoice: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    
    quantity_po: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    quantity_dn: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False,
    )
    
    amount_matched: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    amount_invoice: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    amount_po: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    amount_dn: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Matching criteria results
    item_code_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    description_similarity: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    
    quantity_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    price_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
    )
    
    invoice_line: Mapped["InvoiceLine"] = relationship(
        "InvoiceLine",
        back_populates="match_lines",
    )
    
    def __repr__(self) -> str:
        return f"<MatchLine {self.line_number if hasattr(self, 'line_number') else 'N/A'}>"
    
    @property
    def is_perfect_match(self) -> bool:
        """Check if this is a perfect match."""
        return (
            self.item_code_match
            and self.quantity_match
            and self.price_match
            and self.quantity_variance == Decimal("0")
            and self.amount_variance == Decimal("0")
        )
