// models/matching.py
"""Matching models for 3-way matching."""

import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from models.base import BaseModel

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNote
    from models.purchase_order import PurchaseOrder


class MatchStatus(str, Enum):
    """Match status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    DISPUTED = "disputed"


class MatchType(str, Enum):
    """Match type enumeration."""
    INVOICE_PO = "invoice_po"
    DN_PO = "dn_po"
    INVOICE_DN = "invoice_dn"


class Match(Base, BaseModel):
    """Match record for tracking document matches."""

    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("invoice_id", "po_id", name="uq_match_invoice_po"),
        UniqueConstraint("dn_id", "po_id", name="uq_match_dn_po"),
        UniqueConstraint("invoice_id", "dn_id", name="uq_match_invoice_dn"),
    )

    # Match type discriminator
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Document references (only relevant ones filled based on match_type)
    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    dn_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    po_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Scoring (0.0 to 1.0)
    line_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    amount_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    date_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    # Amount comparison
    po_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    document_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    variance_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)

    # Quantity comparison
    po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=True)
    document_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=True)
    quantity_variance: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=True)

    # Status and decision
    status: Mapped[str] = mapped_column(String(20), default=MatchStatus.PENDING.value, nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(30), nullable=True)
    match_details: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Human review
    reviewed_by: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[str] = mapped_column(String(50), nullable=True)
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", foreign_keys=[invoice_id])
    delivery_note: Mapped["DeliveryNote"] = relationship("DeliveryNote", foreign_keys=[dn_id])
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", foreign_keys=[po_id])

    def __repr__(self) -> str:
        return f"<Match {self.id}: {self.match_type} - {self.status}>"


class MatchLineDetail(Base, BaseModel):
    """Line-level matching details for audit trail."""

    __tablename__ = "match_line_details"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=True)
    po_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    document_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=True)
    document_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    quantity_match: Mapped[bool] = mapped_column(nullable=True)
    price_match: Mapped[bool] = mapped_column(nullable=True)
    line_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="line_details")

    def __repr__(self) -> str:
        return f"<MatchLineDetail {self.item_code}>"


# Add back reference to Match
Match.line_details: Mapped[list] = relationship(
    "MatchLineDetail",
    back_populates="match",
    cascade="all, delete-orphan"
)
