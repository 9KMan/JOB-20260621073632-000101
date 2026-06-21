# models/cross_ref.py
"""CrossRef models — learning loop / cross-reference table."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, Timestamps, UUIDPrimaryKey
from models.enums import MatchConfidence


class CrossRef(Base, UUIDPrimaryKey, Timestamps):
    """
    Learning loop table — records confirmed matches between an invoice header
    and a purchase order header for future automatic anchoring.
    """

    __tablename__ = "cross_refs"

    # ── Invoice ─────────────────────────────────────────────────────────────
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Purchase Order ───────────────────────────────────────────────────────
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Metadata ─────────────────────────────────────────────────────────────
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confirmed_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    match_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confidence: Mapped[MatchConfidence] = mapped_column(
        Enum(MatchConfidence, name="match_confidence"),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    lines: Mapped[list["CrossRefLine"]] = relationship(
        "CrossRefLine",
        back_populates="cross_ref",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "invoice_id", "po_id",
            name="uq_cross_ref_invoice_po",
        ),
        Index("ix_cross_refs_vendor_confirmed", "vendor_code", "confirmed_score"),
    )


class CrossRefLine(Base, UUIDPrimaryKey, Timestamps):
    """
    Learning loop table — records confirmed matches between individual lines
    (invoice line ↔ purchase-order line).
    """

    __tablename__ = "cross_ref_lines"

    cross_ref_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cross_refs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    invoice_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Match metadata ───────────────────────────────────────────────────────
    product_code_match: Mapped[bool] = mapped_column(default=False)
    product_name_match: Mapped[bool] = mapped_column(default=False)
    price_variance_pct: Mapped[float | None] = mapped_column(Numeric(7, 4), nullable=True)
    qty_variance_pct: Mapped[float | None] = mapped_column(Numeric(7, 4), nullable=True)
    line_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    cross_ref: Mapped["CrossRef"] = relationship("CrossRef", back_populates="lines")

    __table_args__ = (
        UniqueConstraint(
            "cross_ref_id", "invoice_line_id", "po_line_id",
            name="uq_cross_ref_line_composite",
        ),
        Index("ix_cross_ref_lines_product", "po_line_id", "product_code_match"),
    )


# ── Forward reference resolution ──────────────────────────────────────────────
from models.invoice import Invoice, InvoiceLine  # noqa: E402, F401
from models.purchase_order import PurchaseOrder, PurchaseOrderLine  # noqa: E402, F401
