// models/cross_ref.py
"""
CrossRef (Cross-Reference) SQLAlchemy model.

The cross-reference table implements the learning loop for the matching engine.
It stores confirmed matches to improve future matching accuracy by learning
from human decisions.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import MatchConfidence, match_confidence_enum


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross-Reference (Learning Loop) table.
    
    Stores learned associations between invoices, POs, and DNs.
    Used by the matching engine to improve accuracy based on
    confirmed human decisions.
    
    Learning levels:
    - 1: Initial/rule-based match
    - 2: Human-confirmed match
    - 3: Repeated confirmation (promoted)
    """

    __tablename__ = "cross_refs"

    # Invoice reference
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Denormalized invoice number for quick lookup",
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Purchase Order reference
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Denormalized PO number for quick lookup",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorder_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Delivery Note reference
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverynotes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Denormalized DN number for quick lookup",
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverynote_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Product linkage
    invoice_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Invoice line SKU",
    )
    po_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="PO line SKU",
    )
    dn_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="DN line SKU",
    )

    # Vendor linkage
    invoice_vendor_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Invoice vendor code",
    )
    po_vendor_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="PO vendor code",
    )

    # Matching metrics
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        doc="Match score at time of confirmation (0-100)",
    )
    confidence: Mapped[MatchConfidence] = mapped_column(
        match_confidence_enum,
        nullable=False,
        doc="Confidence level",
    )

    # Learning data
    learning_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Learning level: 1=rule, 2=confirmed, 3=promoted",
    )
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this match was confirmed",
    )
    rejection_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this match was rejected",
    )

    # Decision tracking
    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Matching decision: approved, rejected, etc.",
    )
    decided_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who made the decision",
    )
    decided_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date of decision",
    )

    # Promotion tracking
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this match has been promoted to higher learning level",
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of promotion",
    )
    promoted_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved promotion",
    )

    # Active status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether this cross-reference is active",
    )
    deactivation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for deactivation if applicable",
    )

    # JSON metadata for extensibility
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        doc="Additional match metadata",
    )

    # Weight for scoring algorithm
    weight: Mapped[float] = mapped_column(
        Numeric(5, 3),
        nullable=False,
        default=1.0,
        doc="Weight factor for scoring (1.0 default)",
    )

    __table_args__ = (
        Index("ix_xref_invoice_vendor", "invoice_number", "invoice_vendor_code"),
        Index("ix_xref_po_vendor", "po_number", "po_vendor_code"),
        Index("ix_xref_sku_match", "invoice_sku", "po_sku"),
        Index("ix_xref_learning", "learning_level", "is_active"),
        Index("ix_xref_confidence", "confidence", "match_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef(id={self.id}, "
            f"invoice={self.invoice_number}, "
            f"po={self.po_number}, "
            f"level={self.learning_level})>"
        )
