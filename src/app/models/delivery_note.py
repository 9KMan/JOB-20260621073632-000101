// src/app/models/delivery_note.py
"""Delivery Note models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    String,
    Numeric,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.match import Match

DN_STATUS = Enum(
    "DN_STATUS",
    ["DRAFT", "DISPATCHED", "IN_TRANSIT", "DELIVERED", "PARTIAL", "CANCELLED"],
)


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery Note model."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DN_STATUS] = mapped_column(
        SQLEnum(DN_STATUS, name="dn_status"),
        default=DN_STATUS.DRAFT,
        nullable=False,
    )
    po_reference: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
        foreign_keys="Match.delivery_note_id",
    )

    __table_args__ = (
        Index("ix_dn_supplier_status", "supplier_id", "status"),
        Index("ix_dn_delivery_date", "delivery_date"),
        Index("ix_dn_po_reference", "po_reference"),
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_dnl_dn_id", "delivery_note_id"),
        Index("ix_dnl_product_code", "product_code"),
    )
