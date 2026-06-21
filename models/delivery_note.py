// models/delivery_note.py
"""Delivery Note model definition.

This module defines the DeliveryNote SQLAlchemy model representing
incoming delivery notes that provide receiving information for matching.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    pass


class DeliveryNoteLine(Base):
    """Delivery Note Line item.

    Represents individual line items within a delivery note.
    """

    __tablename__ = "dn_lines"

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item number",
    )

    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Item/product code",
    )
    item_description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        doc="Item description",
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Unit price (if available)",
    )

    uom: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
        doc="Unit of measure",
    )

    po_line_reference: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to PO line",
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_item_code", "item_code"),
    )


class DeliveryNote(Base):
    """Delivery Note model.

    Represents a delivery note (goods received note) that provides
    receiving information for matching with invoices and POs.

    Attributes:
        id: UUID primary key
        dn_number: Unique delivery note number
        vendor_code: Vendor/supplier identifier
        vendor_name: Vendor name
        po_reference: Reference to purchase order
        receipt_date: Date goods were received
        status: Current status
        total_amount: Total delivery note amount
        currency: Currency code
        warehouse_location: Receiving warehouse/location
        received_by: Person who received the goods
        notes: Additional notes
        is_ocr_processed: Whether OCR has been processed
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "delivery_notes"

    # Primary identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique delivery note number",
    )

    # Vendor information
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Vendor code",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name",
    )

    # Reference to PO
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Reference to purchase order number",
    )

    # Date fields
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date goods were received",
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Total DN amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="received",
        nullable=False,
        index=True,
        doc="Current DN status",
    )

    # Receiving information
    warehouse_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Receiving warehouse/location",
    )
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Person who received the goods",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # OCR fields
    is_ocr_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether OCR has been processed",
    )

    # Relationships
    lines: Mapped[list[DeliveryNoteLine]] = relationship(
        "DeliveryNoteLine",
        back_populates="dn",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_dns_vendor_date", "vendor_code", "receipt_date"),
        Index("ix_dns_po_reference", "po_reference"),
        Index("ix_dns_status", "status"),
    )

    def __repr__(self) -> str:
        """String representation of DeliveryNote."""
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, vendor={self.vendor_code})>"

    @property
    def is_processed(self) -> bool:
        """Check if DN is processed for matching."""
        return self.status == "processed"


# Import uuid
import uuid
