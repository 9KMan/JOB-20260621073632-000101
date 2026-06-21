// models/delivery_note.py
"""Delivery Note and DeliveryNoteLine SQLAlchemy models."""

from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.cross_ref import CrossRef


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note (GR/Shipping Notification) header model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_supplier_number", "supplier_number"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_created_at", "created_at"),
        Index("ix_delivery_notes_external_reference", "external_reference"),
        {
            "schema": "public",
        },
    )

    # Delivery note identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Delivery note number",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="External system reference (ERP, WMS)",
    )

    # PO reference
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Referenced PO number",
    )
    po_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        doc="Referenced PO ID",
    )

    # Supplier information
    supplier_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Internal supplier identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Supplier name",
    )
    supplier_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Supplier account number",
    )

    # Company/Legal Entity
    company_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Company code",
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Actual/scheduled delivery date",
    )
    posting_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date posted to system",
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total delivery note amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.CONFIRMED,
        doc="Delivery note status",
    )

    # Logistics
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Carrier name",
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Tracking number",
    )
    number_of_packages: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Number of packages",
    )

    # Additional metadata
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Delivery note description",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # User tracking
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created the delivery note",
    )
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who confirmed receipt",
    )
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when received",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, status={self.status})>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_product_code", "product_code"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        {
            "schema": "public",
        },
    )

    # Parent reference
    dn_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent delivery note ID",
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    external_line_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="External system line reference",
    )

    # Product/Service information
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product or service code",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Delivered quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Pricing (for reference)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Unit price (from PO for reference)",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total line amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line status",
    )

    # PO Line reference
    po_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        doc="Matched PO line ID",
    )
    matched_po_line_number: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Matched PO line number for reference",
    )

    # Quality
    quality_check_passed: Mapped[bool | None] = mapped_column(
        nullable=True,
        doc="Quality check status",
    )
    batch_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Batch/lot number",
    )

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, dn_id={self.dn_id}, line={self.line_number})>"
