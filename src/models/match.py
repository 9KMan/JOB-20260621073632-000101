// src/models/match.py
"""Match and Match Line models for 3-way matching."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.models.base import Base, BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.user import User


class MatchDecision(str, enum.Enum):
    """Match decision outcomes."""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    REJECTED = "rejected"


class MatchType(str, enum.Enum):
    """Type of match relationship."""
    PO_INVOICE = "po_invoice"
    PO_DELIVERY = "po_delivery"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class Match(Base, BaseModel):
    """Match record linking PO, Invoice, and/or Delivery Note."""
    
    __tablename__ = "matches"
    
    match_type: Mapped[str] = mapped_column(
        SQLEnum(MatchType),
        nullable=False,
        index=True
    )
    decision: Mapped[str] = mapped_column(
        SQLEnum(MatchDecision),
        default=MatchDecision.PENDING,
        nullable=False,
        index=True
    )
    
    # Document references
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
    
    # Matching scores
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Amount comparisons
    po_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    invoice_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    delivery_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    # Human review
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Processing
    processing_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    auto_approved: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
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
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="matches_reviewed",
        foreign_keys=[reviewed_by]
    )
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Match(id={self.id}, type={self.match_type}, decision={self.decision})>"


class MatchLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Match line for item-level matching details."""
    
    __tablename__ = "match_lines"
    
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Line references (optional, depending on match type)
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    delivery_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Matched items
    item_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Quantities
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    invoice_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    delivery_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    
    # Prices
    po_unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True
    )
    invoice_unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True
    )
    
    # Scores
    quantity_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    price_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Variance
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False
    )
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    
    # Line totals
    po_line_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    invoice_line_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    # Match status at line level
    is_matched: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )
    variance_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<MatchLine(id={self.id}, item={self.item_code})>"
