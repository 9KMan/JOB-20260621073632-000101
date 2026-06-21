# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery note header model."""

    __tablename__ = "delivery_notes"

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # DN Details
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    dn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Reference to PO
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="received",
        nullable=False,
        index=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft Delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_note",
        lazy="selectin",
    )


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery note line item model."""

    __tablename__ = "delivery_note_lines"

    # Parent
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product Reference
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Reference to PO Line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_line", "delivery_note_id", "line_number"),
    )
