# models/delivery_note.py
"""Delivery Note model."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import POLine


class DeliveryNote(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Delivery note header model."""

    __tablename__ = "delivery_notes"

    dn_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False, index=True)

    # ERP reference
    erp_dn_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_system: Mapped[str] = mapped_column(String(50), default="erp", nullable=False)

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dn_vendor_date", "vendor_code", "delivery_date"),
        {"schema": None},
    )


class DeliveryNoteLine(Base, UUIDPrimaryKey):
    """Delivery note line item model."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False)

    # Additional data
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    po_line: Mapped["POLine | None"] = relationship("POLine", back_populates="delivery_lines")
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine", back_populates="delivery_line"
    )

    __table_args__ = (
        UniqueConstraint("delivery_note_id", "line_number", name="uq_dn_line_number"),
        Index("ix_dn_lines_po", "po_line_id"),
    )
