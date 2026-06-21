# models/cross_ref.py
"""CrossRef — learning loop / cross-reference table for confirmed matches."""

import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import (
    Numeric,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Learning loop table — records confirmed matches between document entities
    so that future matches can use this information to improve scoring.

    When an invoice line is matched to a PO line (and confirmed by an
    accountant or auto-approved), a CrossRef record is created. The matching
    engine can later use these records as anchors for future matches, promoting
    them when the confidence score crosses a promotion threshold.

    Attributes
    ----------
    vendor_id : str
        Vendor this cross-reference applies to.
    invoice_sku : str | None
        SKU from the invoice line (if available).
    po_sku : str | None
        SKU from the PO line (if available).
    invoice_description : str | None
        Partial description from the invoice line.
    po_description : str | None
        Partial description from the PO line.
    invoice_uom : str | None
        Unit of measure from the invoice line.
    po_uom : str | None
        Unit of measure from the PO line.
    match_count : int
        Number of times this cross-reference has been used in a successful match.
    confirmation_count : int
        Number of times this cross-reference has been manually confirmed.
    is_promoted : bool
        Whether this cross-reference has been promoted to a higher confidence tier.
    promoted_at : datetime | None
        Timestamp when this record was promoted.
    is_active : bool
        Whether this record is currently active (soft-disable for corrections).
    source : str
        How this record was created: 'manual', 'auto_approved', 'one_click'.
    notes : str | None
        Free-text notes.
    """

    __tablename__ = "cross_refs"

    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # SKU fields (partial match candidates)
    invoice_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Description fields (partial / fuzzy match candidates)
    invoice_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    po_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # UoM fields
    invoice_uom: Mapped[str | None] = mapped_column(String(20), nullable=True)
    po_uom: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Scoring / usage
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Promotion state
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="auto_approved",
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    # Foreign keys to the canonical records that generated this cross-ref
    source_invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "vendor_id",
            "invoice_sku",
            "po_sku",
            name="uq_cross_ref_vendor_skus",
        ),
        Index("ix_cross_refs_vendor_active", "vendor_id", "is_active"),
        Index("ix_cross_refs_promoted", "is_promoted", "is_active"),
    )
