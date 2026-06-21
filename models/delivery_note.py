"""DeliveryNote and DeliveryNoteLine ORM models."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus


class DeliveryNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Goods-received note, either from ERP or OCR ingestion."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    warehouse: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        String(32), nullable=False, default=DocumentStatus.INGESTED, index=True
    )
    is_ocr: Mapped[bool] = mapped_column(default=False, nullable=False)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ux_delivery_notes_vendor_dn_no", "vendor_id", "dn_number", unique=True),
    )


class DeliveryNoteLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Single goods-received line linked to a purchase order line (best effort)."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    received_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")

    delivery_note: Mapped[DeliveryNote] = relationship(
        "DeliveryNote", back_populates="lines"
    )

    __table_args__ = (
        Index(
            "ux_delivery_note_lines_dn_line_no",
            "delivery_note_id",
            "line_number",
            unique=True,
        ),
    )
