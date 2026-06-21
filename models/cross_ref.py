# models/cross_ref.py
"""CrossRef SQLAlchemy model for the learning/matching loop."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CommonMixin
from models.enums import MatchDecision, MatchStatus


class CrossRef(Base, CommonMixin):
    """Cross Reference model for tracking match history and learning.

    This table implements the learning loop by recording:
    - Match patterns (invoice-PO-DN combinations)
    - Confidence scores and decisions
    - User confirmations/corrections
    - Promotion rules for future matching
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_id", "invoice_id"),
        Index("ix_cross_ref_po_id", "po_id"),
        Index("ix_cross_ref_dn_id", "dn_id"),
        Index("ix_cross_ref_confirmed_at", "confirmed_at"),
        Index("ix_cross_ref_match_hash", "match_hash"),
        {"schema": None},
    )

    # Document references
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    invoice_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    po_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Match attributes
    match_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Hash of match attributes for quick lookup",
    )
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Calculated match score (0-1)",
    )
    price_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    quantity_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    date_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    description_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    # Match decision
    decision: Mapped[MatchDecision] = mapped_column(
        nullable=False,
    )
    status: Mapped[MatchStatus] = mapped_column(
        nullable=False,
        default=MatchStatus.PENDING,
    )

    # Learning tracking
    is_confirmed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    confirmed_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    confirmation_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="How was this confirmed: user, system, auto",
    )

    # Promotion tracking
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rejection_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    promotion_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="0=new, 1=learned, 2=trusted, 3=canonical",
    )
    is_promotion_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Variance details
    price_variance: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    quantity_variance: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )

    # Attributes for learning
    vendor_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # User notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="cross_refs",
        foreign_keys=[invoice_id],
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
        foreign_keys=[po_id],
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
        foreign_keys=[dn_id],
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef INV:{self.invoice_number} PO:{self.po_number} "
            f"DN:{self.dn_number} Score:{self.match_score}>"
        )

    @property
    def is_trusted(self) -> bool:
        """Check if this match is trusted (can be used for auto-match)."""
        return self.promotion_level >= 2 or self.confirmation_count >= 3

    @property
    def is_canonical(self) -> bool:
        """Check if this is a canonical (authoritative) match."""
        return self.promotion_level >= 3

    def should_auto_match(self, min_score: float = 0.85) -> bool:
        """Determine if this match should be used for auto-matching.

        Args:
            min_score: Minimum score threshold

        Returns:
            bool: True if should auto-match
        """
        if self.decision == MatchDecision.REJECTED:
            return False
        if self.rejection_count > 0:
            return False
        return self.match_score >= min_score and (self.is_confirmed or self.is_trusted)

    def promote(self) -> bool:
        """Promote this cross-reference to the next level.

        Returns:
            bool: True if promotion occurred
        """
        if self.promotion_level < 3:
            self.promotion_level += 1
            return True
        return False

    def confirm(self, confirmed_by: str | None = None) -> None:
        """Confirm this match.

        Args:
            confirmed_by: User who confirmed
        """
        self.is_confirmed = True
        self.confirmed_by = confirmed_by
        self.confirmation_count += 1
        self.promote()

    def reject(self) -> None:
        """Reject this match."""
        self.rejection_count += 1
        self.is_confirmed = False
        if self.rejection_count >= 3:
            self.is_promotion_active = False
