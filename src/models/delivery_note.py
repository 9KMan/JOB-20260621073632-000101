# src/models/delivery_note.py
"""Delivery Note model and related types."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.cross_ref import CrossRef


class DeliveryNote(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Delivery Note model representing supplier deliveries.
    
    Attributes:
        id: Unique identifier (UUID)
        dn_number: Delivery note number
        supplier_id: External supplier identifier
        supplier_name: Supplier's business name
        po_id: Linked purchase order reference
        carrier: Shipping carrier name
        tracking_number: Tracking/shipping number
        shipment_date: Date goods were shipped
        delivery_date: Date goods were/will be delivered
        status: Current delivery note status
        notes: Additional notes
        metadata: JSON field for additional data
    """
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_supplier_id", "supplier_id"),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_shipment_date", "shipment_date"),
        Index("ix_delivery_notes_status", "status"),
    )
    
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    shipment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "issued",
            "in_transit",
            "delivered",
            "partially_delivered",
            "received",
            "cancelled",
            name="delivery_note_status",
            create_constraint=True,
        ),
        nullable=False,
        default="draft",
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
    )


class DeliveryNoteLine(UUIDMixin, TimestampMixin, Base):
    """
    Individual line item on a delivery note.
    
    Attributes:
        id: Unique identifier (UUID)
        dn_id: Parent delivery note reference
        line_number: Line item sequence number
        description: Line item description
        product_code: Supplier's product/SKU code
        quantity: Delivered quantity
        unit_of_measure: UOM
        po_line_id: Linked PO line reference
        received_flag: Whether goods have been received into warehouse
        received_at: Timestamp when goods were received
    """
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        Index("ix_delivery_note_lines_product_code", "product_code"),
    )
    
    dn_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    po_line_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    received_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
        back_populates="delivery_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_line",
    )
