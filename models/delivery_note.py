# models/delivery_note.py
"""Delivery Note and DeliveryNoteLine SQLAlchemy models."""

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
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Delivery Note header model.
    
    Represents a delivery note (DN) from the vendor or logistics.
    """
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
        Index("ix_delivery_notes_po_id", "po_id"),
    )
    
    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # PO Reference
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # DN Identification
    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(50),
        nullable=False,
        default=DeliveryNoteStatus.CONFIRMED,
    )
    
    # Financial Summary
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Source Information
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="erp")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Logistics
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    number_of_packages: Mapped[int | None] = mapped_column(nullable=True)
    
    # Additional Fields
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Delivery Note Line Item model.
    
    Represents individual line items on a delivery note.
    """
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "dn_id", "line_number", unique=True),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        Index("ix_delivery_note_lines_sku", "sku"),
    )
    
    # Parent Delivery Note
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # PO Line Reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Line Information
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Product Information
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    
    # Pricing (optional for DN)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    line_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        foreign_keys=[po_line_id],
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="dn_line",
        foreign_keys="InvoiceLine.dn_line_id",
    )
