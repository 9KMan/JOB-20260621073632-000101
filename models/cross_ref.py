// models/cross_ref.py
"""CrossRef — learning loop / cross-reference table for match history."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryMixin

if TYPE_CHECKING:
    from models.purchase_order import POLine
    from models.invoice import InvoiceLine


class CrossRef(Base, UUIDPrimaryMixin, TimestampMixin):
    """
    Cross-reference record used by the learning loop.

    Records every confirmed or rejected match between an invoice line
    and a PO line so the system can:
      1. Detect duplicate matches
      2. Learn from human corrections
      3. Promote frequently confirmed pairs to automatic approval

    A record with `is_promoted=True` is trusted implicitly by the
    scoring engine (bonus confidence points).
    """

    __tablename__ = "cross_refs"
    __table_args__ = (
        Index("ix_cross_refs_po_line_id", "po_line_id"),
        Index("ix_cross_refs_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_refs_sku", "sku"),
        Index("ix_cross_refs_vendor_number", "vendor_number"),
        Index("ix_cross_refs_is_promoted", "is_promoted"),
        # Unique constraint: only one active cross_ref per invoice_line
        Index(
            "ix_cross_refs_invoice_line_active",
            "invoice_line_id",
            "is_active",
            unique=True,
        ),
    )

    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    vendor_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Match statistics
    confirmations: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    rejections: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Learning state
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False, index=True
    )
    is_promoted: Mapped[bool] = mapped_column(
        default=False, nullable=False, index=True
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_learned: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="System has learned this pair from corrections"
    )

    # Metadata from the match that created this record
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    matched_by: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="'anchoring' | 'cascade' | 'manual'"
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    po_line: Mapped["POLine | None"] = relationship("POLine")
    invoice_line: Mapped["InvoiceLine | None"] = relationship("InvoiceLine")
