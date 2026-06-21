# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, Timestamps, UUIDPrimaryKey
from models.enums import DeliveryNoteStatus


class DeliveryNote(Base, UUIDPrimaryKey, Timestamps):
    """Top-level delivery note entity (from ERP or OCR)."""

    __tablename__ = "delivery_notes"

    # ── Vendor ─────────────────────────────────────────────────────────────
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Reference fields ────────────────────────────────────────────────────
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    dn_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    receipt_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Source ──────────────────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(
        String(20),
        default="erp",
        nullable=False,
    )  # 'erp' | 'ocr'

    # ── Status ──────────────────────────────────────────────────────────────
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        Enum(DeliveryNoteStatus, name="delivery_note_status"),
        default=DeliveryNoteStatus.RECEIVED,
        nullable=False,
        index=True,
    )

    # ── ERP ─────────────────────────────────────────────────────────────────
    erp_dn_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_status", "vendor_code", "status"),
    )


class DeliveryNoteLine(Base, UUIDPrimaryKey, Timestamps):
    """Line-level detail for a delivery note."""

    __tablename__ = "delivery_note_lines"

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Product / SKU ───────────────────────────────────────────────────────
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Quantities ──────────────────────────────────────────────────────────
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Matching ────────────────────────────────────────────────────────────
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_id_number", "dn_id", "line_number"),
    )


# ── Forward reference resolution ──────────────────────────────────────────────
from models.purchase_order import PurchaseOrder, PurchaseOrderLine  # noqa: E402, F401
