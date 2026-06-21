# src/models/delivery_note.py
"""Delivery Note model for AP Automation Core Engine.

Represents delivery notes (goods received notes) that confirm
goods have been delivered and can be used for three-way matching.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.cross_ref import CrossRef


class DeliveryNoteLine(TimestampMixin, UUIDMixin, Base):
    """Individual line item on a delivery note.

    Represents a delivered item that can be matched against
    PO lines and invoice lines.
    """

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to parent delivery note",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure (e.g., EA, KG, M)",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched PO line ID",
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched invoice line ID",
    )
    received_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of person who received the goods",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp when goods were received",
    )
    quality_check_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether quality check was passed",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes for this line",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
        foreign_keys=[delivery_note_id],
    )

    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
    )


class DeliveryNote(TimestampMixin, SoftDeleteMixin, UUIDMixin, Base):
    """Delivery Note model representing goods received.

    Also known as Goods Received Note (GRN), this document
    confirms physical delivery and is used for three-way matching.
    """

    __tablename__ = "delivery_notes"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Vendor/supplier identifier from ERP",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor/supplier name",
    )

    # Delivery note identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Delivery note number from vendor/carrier",
    )
    po_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Reference to PO number",
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched purchase order ID",
    )

    # Dates
    shipment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were shipped",
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date goods were delivered",
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date goods were received in system",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="received",
        doc="Delivery note status",
    )

    # ERP reference
    erp_dn_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Delivery note ID in the ERP system",
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
        doc="Source system identifier",
    )

    # Carrier information
    carrier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Name of shipping carrier",
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Shipment tracking number",
    )

    # Additional metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )
    received_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of person who received the goods",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        Index("ix_delivery_notes_erp_dn_id", "erp_dn_id"),
        Index("ix_delivery_notes_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} for PO {self.po_reference}>"
