// models/delivery_note.py
"""Delivery Note and DeliveryNoteLine SQLAlchemy models.

This module defines the DeliveryNote and DeliveryNoteLine database models
for storing delivery note data from ERP/warehouse systems.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model representing a delivery from vendor.

    Attributes:
        dn_number: Unique delivery note number
        vendor_id: External vendor identifier
        vendor_name: Vendor display name
        po_reference: Referenced PO number
        delivery_date: Date of delivery
        received_by: Person who received delivery
        subtotal: DN subtotal before tax
        tax_amount: Tax amount
        total_amount: Total DN amount
        currency: Currency code (ISO 4217)
        status: Current document status
        notes: Additional notes
        lines: Delivery note line items
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        UniqueConstraint("dn_number", "vendor_id", name="uq_dn_number_vendor"),
    )

    # Core fields
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
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

    # Reference fields
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        default_factory=lambda: date.today(),
        nullable=False,
    )

    # Financial fields
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Metadata
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    condition: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.delivery_date}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line item model.

    Represents individual line items on a delivery note for
    line-level matching with purchase orders and invoices.

    Attributes:
        delivery_note_id: Parent delivery note foreign key
        line_number: Line item number
        description: Line item description
        quantity: Delivered quantity
        unit_of_measure: Unit of measure
        unit_price: Price per unit (from PO)
        total_price: Line total
        sku: Product SKU
        po_line_id: Matching PO line ID
        matched_quantity: Quantity matched to PO
        batch_number: Batch/lot number
        expiry_date: Expiry date for perishable goods
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        Index("ix_delivery_note_lines_sku", "sku"),
    )

    # Foreign key
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Quantity and pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    # Matching
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    match_score: Mapped[int | None] = mapped_column(
        default=None,
        nullable=True,
    )

    # Metadata
    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    condition: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.description[:30]}>"
