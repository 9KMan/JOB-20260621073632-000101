# models/delivery_note.py
"""Delivery Note model definition."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrder
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model representing goods received from supplier."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_vendor_number", "vendor_number"),
        Index("ix_dn_dn_number", "dn_number"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_receipt_date", "receipt_date"),
    )

    # Header fields
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        Enum(DeliveryNoteStatus),
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Reference to PO
    purchase_order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    purchase_order_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Additional fields
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ERP reference
    erp_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.vendor_number}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dnl_dn_id", "delivery_note_id"),
        Index("ix_dnl_line_number", "line_number"),
    )

    delivery_note_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    item_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Reference to PO line
    purchase_order_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Reference to invoice line (for tracking which invoice matched)
    invoice_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    is_invoiced: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"
