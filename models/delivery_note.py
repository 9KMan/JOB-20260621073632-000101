# models/delivery_note.py
"""Delivery note and delivery note line models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import Currency, DeliveryNoteStatus, LineType


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note header model."""

    __tablename__ = "delivery_notes"

    # Vendor Information
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # DN Details
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    dn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(30),
        default=DeliveryNoteStatus.CONFIRMED.value,
        nullable=False,
        index=True
    )
    
    # Reference to PO
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Delivery Info
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ERP Reference
    erp_dn_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_note",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_notes_po_date", "purchase_order_id", "dn_date"),
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery note line item model."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    line_type: Mapped[str] = mapped_column(String(20), default=LineType.STANDARD.value, nullable=False)
    
    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    
    # Product Reference
    product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Reference to PO Line
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # ERP Reference
    erp_line_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship("DeliveryNote", back_populates="lines")
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        lazy="selectin",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_note_lines_dn_number", "delivery_note_id", "line_number"),
    )


from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.invoice import Invoice, InvoiceLine
