// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine database models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, TimestampMixin):
    """Delivery note header model.

    Represents a delivery note (packing slip) from a vendor.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        UniqueConstraint("vendor_number", "dn_number", name="uq_vendor_dn"),
        {"schema": "public"},
    )

    # DN identification
    dn_number: Mapped[str] = mapped_column(String(50), nullable=False)
    external_dn_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Vendor information
    vendor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Reference to PO
    po_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    po_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public.purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Dates
    delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.SUBMITTED,
        index=True,
    )

    # Additional data
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Lines relationship
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} from {self.vendor_name}>"


class DeliveryNoteLine(Base, TimestampMixin):
    """Delivery note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        {"schema": "public"},
    )

    # Foreign key
    dn_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public.delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # PO Line reference
    po_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public.purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Product reference
    product_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Unit of measure
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"
