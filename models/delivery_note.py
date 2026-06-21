# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, BaseMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, BaseMixin):
    """Delivery Note (Goods Receipt) model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        UniqueConstraint("dn_number", name="uq_delivery_notes_dn_number"),
    )

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Reference to PO
    po_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # DN Details
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.RECEIVED,
        index=True,
    )

    # External References
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    erp_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Receiving Information
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    receiving_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Financial Information
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Additional Data
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DeliveryNoteLine(Base, BaseMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
    )

    # Parent Delivery Note
    dn_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product Information
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantity
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )

    # PO Line Reference
    po_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Line Status
    is_accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_exception: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    exception_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Pricing (for reference)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
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
        return f"<DeliveryNoteLine {self.id} line={self.line_number} qty={self.quantity_delivered}>"
