// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model for goods received."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
    )

    # Vendor Information
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Delivery Note Details
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_date: Mapped[Date] = mapped_column(Date, nullable=False)
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Reference
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_system: Mapped[str] = mapped_column(String(50), default="warehouse", nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.SUBMITTED.value,
        nullable=False,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.vendor_name}>"


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Product Information
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )

    # PO Line Reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
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

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"


from models.purchase_order import PurchaseOrderLine  # noqa: E402, F401
