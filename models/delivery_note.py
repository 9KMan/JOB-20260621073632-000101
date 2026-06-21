# models/delivery_note.py
"""
DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes for three-way matching (PO + DN + Invoice).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Delivery Note model representing deliveries from vendors.
    
    DN records are used for three-way matching alongside POs and invoices.
    They track what was actually delivered.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_vendor_dn_number", "vendor_id", "dn_number", unique=True),
        {"schema": None},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Core Fields
    # ─────────────────────────────────────────────────────────────────────────
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor/Supplier identifier",
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor display name",
    )
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Delivery note number",
    )
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated purchase order ID",
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Delivery date",
    )
    received_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were received",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Financial Fields
    # ─────────────────────────────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="DN total amount",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────────
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(50),
        nullable=False,
        default=DeliveryNoteStatus.ISSUED,
        index=True,
        doc="Current DN status",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────────────────
    erp_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="ERP system reference",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    received_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who received the delivery",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        backref="delivery_notes",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} from {self.vendor_id}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """
    Delivery Note Line item model.
    
    Represents individual line items on a DN for line-level matching.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        Index("ix_delivery_note_lines_sku", "sku"),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Foreign Keys
    # ─────────────────────────────────────────────────────────────────────────
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Associated PO line ID",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Line Details
    # ─────────────────────────────────────────────────────────────────────────
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number on DN",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product/Item SKU",
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    accepted_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Accepted quantity (after inspection)",
    )
    rejected_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Rejected quantity",
    )
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Pricing (for reference, usually inherited from PO)
    # ─────────────────────────────────────────────────────────────────────────
    unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Unit price",
    )
    line_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Line total",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────────────────────────────
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
        backref="matched_dn_lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
