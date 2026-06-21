# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning loop / cross-reference table."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import LearningStatus, MatchConfidence


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference table for learning confirmed matches.

    This table stores learned associations between PO and invoice data
    to improve future matching accuracy.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_po_vendor_product", "po_vendor_id", "po_product_code"),
        Index("ix_cross_ref_invoice_vendor_product", "invoice_vendor_id", "invoice_product_code"),
        Index("ix_cross_ref_learning_status", "learning_status"),
        {"schema": None},
    )

    # Product identifiers
    po_vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    po_vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    po_product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    po_product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    invoice_vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    invoice_vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    invoice_product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Matched pricing (from confirmed match)
    matched_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    matched_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )

    # Match statistics
    match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Confidence and learning
    confidence: Mapped[str] = mapped_column(
        String(20),
        default=MatchConfidence.MEDIUM.value,
        nullable=False,
    )
    learning_status: Mapped[str] = mapped_column(
        String(20),
        default=LearningStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    promotion_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    demotion_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Manual override
    is_manually_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_manually_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Variance tolerances learned
    price_tolerance_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    qty_tolerance_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # Related entities
    related_cross_ref_ids: Mapped[list[str] | None] = mapped_column(
        Text, nullable=True
    )  # JSON array of UUIDs

    def __repr__(self) -> str:
        return (
            f"<CrossRef PO:{self.po_product_code} -> "
            f"INV:{self.invoice_product_code} ({self.match_count} matches)>"
        )

    def update_learning_stats(
        self,
        match_score: float,
        unit_price: Decimal | None = None,
        quantity: Decimal | None = None,
    ) -> None:
        """Update learning statistics after a confirmed match.

        Args:
            match_score: Score of this match
            unit_price: Unit price from this match
            quantity: Quantity from this match
        """
        self.match_count += 1
        self.total_match_score += match_score
        self.average_match_score = self.total_match_score / self.match_count
        self.last_match_score = match_score
        self.last_matched_at = datetime.now(timezone.utc)

        if unit_price is not None:
            self.matched_unit_price = unit_price
        if quantity is not None:
            self.matched_quantity = quantity

    def update_confidence(self, new_confidence: MatchConfidence) -> None:
        """Update confidence level based on match history.

        Args:
            new_confidence: New confidence level
        """
        old_confidence = self.confidence
        self.confidence = new_confidence.value

        if new_confidence == MatchConfidence.HIGH and old_confidence != MatchConfidence.HIGH:
            self.promotion_count += 1
            self.learning_status = LearningStatus.PROMOTED.value
        elif new_confidence == MatchConfidence.LOW and old_confidence == MatchConfidence.HIGH:
            self.demotion_count += 1
            self.learning_status = LearningStatus.DEMOTED.value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            dict: Dictionary representation of cross reference
        """
        return {
            "id": str(self.id),
            "po_vendor_id": self.po_vendor_id,
            "po_vendor_name": self.po_vendor_name,
            "po_product_code": self.po_product_code,
            "po_product_name": self.po_product_name,
            "invoice_vendor_id": self.invoice_vendor_id,
            "invoice_vendor_name": self.invoice_vendor_name,
            "invoice_product_code": self.invoice_product_code,
            "invoice_product_name": self.invoice_product_name,
            "matched_unit_price": float(self.matched_unit_price) if self.matched_unit_price else None,
            "matched_quantity": float(self.matched_quantity) if self.matched_quantity else None,
            "match_count": self.match_count,
            "average_match_score": self.average_match_score,
            "last_match_score": self.last_match_score,
            "last_matched_at": self.last_matched_at.isoformat() if self.last_matched_at else None,
            "confidence": self.confidence,
            "learning_status": self.learning_status,
            "is_active": self.is_active,
        }
