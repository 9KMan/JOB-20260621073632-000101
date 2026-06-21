// src/app/models/match.py
"""
Match Result and Match Decision models.
"""
from decimal import Decimal
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class MatchDecision(str, Enum):
    """Match decision enumeration."""
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_REVIEW = "PENDING_REVIEW"
    DISPUTED = "DISPUTED"


class MatchResult(Base, UUIDPrimaryKey, TimestampMixin):
    """Result of matching between Invoice, Delivery Note, and Purchase Order."""

    __tablename__ = "match_results"

    # Document references
    invoice_id = Column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    po_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True
    )
    dn_id = Column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True
    )

    # Match scores (0.0 to 1.0)
    line_match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    amount_match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    date_match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    overall_match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    # Match decision
    decision = Column(
        SQLEnum(MatchDecision),
        default=MatchDecision.PENDING_REVIEW,
        nullable=False,
        index=True,
    )

    # Matched amounts
    invoice_amount = Column(Numeric(15, 2), nullable=False)
    po_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Matched quantities
    invoice_quantity = Column(Numeric(15, 3), nullable=False)
    po_quantity = Column(Numeric(15, 3), nullable=True)
    dn_quantity = Column(Numeric(15, 3), nullable=True)
    variance_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)

    # Variance details
    price_variance = Column(Numeric(15, 4), nullable=True)
    quantity_variance = Column(Numeric(15, 3), nullable=True)
    variance_reason = Column(Text, nullable=True)

    # Confirmation
    confirmed_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_notes = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, confirmed, rejected, resolved
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="match_results",
    )
    purchase_order = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="matched_invoices",
    )
    delivery_note = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="matched_delivery_notes",
    )
    confirmed_by_user = relationship(
        "User",
        foreign_keys=[confirmed_by_id],
        back_populates="match_confirmations",
    )

    def __repr__(self) -> str:
        return f"<MatchResult {self.id}: {self.overall_match_score}>"

    @property
    def is_confirmed(self) -> bool:
        """Check if match is confirmed."""
        return self.status == "confirmed" and self.confirmed_by_id is not None

    @property
    def is_variance(self) -> bool:
        """Check if there's a variance."""
        return self.variance_amount != Decimal("0.00") or self.variance_quantity != Decimal("0.000")

    def get_layer(self) -> int:
        """Get the matching layer (1, 2, or 3)."""
        if self.po_id and not self.dn_id:
            return 1  # Layer 1: Invoice -> PO
        elif self.po_id and self.dn_id and not self.invoice_id:
            return 1  # Layer 1: DN -> PO
        elif self.po_id and self.dn_id:
            return 2  # Layer 2: Full 3-way match
        elif self.invoice_id and self.dn_id:
            return 2  # Layer 2: Invoice -> DN
        return 3  # Layer 3: Balance resolution
