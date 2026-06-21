# models/delivery_note.py
"""Delivery Note model definition."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Delivery Note model representing supplier deliveries.

    Attributes:
        id: UUID primary key
        dn_number: Unique DN number
        vendor_id: Supplier/vendor identifier
        vendor_name: Supplier name
        delivery_date: Date of delivery
        po_reference: Reference to linked PO
        status: Current DN status
        notes: Additional notes
        metadata: Additional flexible fields
        lines: Child DN lines
    """

    __tablename__ = "delivery_notes"

    # Core DN fields
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # PO Reference
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_date", "vendor_id", "delivery_date"),
        Index("ix_delivery_notes_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.vendor_name}>"


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual line items on a Delivery Note.

    Attributes:
        id: UUID primary key
        dn_id: Parent DN reference
        line_number: Line item number
        description: Line item description
        sku: Product SKU
        quantity: Delivered quantity
        unit_of_measure: UOM
        po_line_reference: Reference to matched PO line
        matched_po_line_id: Reference to matched PO line
        matched_invoice_line_id: Reference to matched invoice line
        status: Line status
    """

    __tablename__ = "delivery_note_lines"

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Quantity
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )

    # Matching
    po_line_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_line", "dn_id", "line_number"),
        Index("ix_dn_lines_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description} x {self.quantity}>"
