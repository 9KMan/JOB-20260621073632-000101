# models/delivery_note.py
"""Delivery Note model for AP Automation Engine."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from models.cross_ref import CrossRef
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model representing goods received.

    Attributes:
        dn_number: Unique delivery note number
        po_id: Reference to linked PO
        po_number: PO number for quick reference
        vendor_id: External vendor identifier
        vendor_name: Name of the vendor
        receipt_date: Date goods were received
        subtotal: DN subtotal
        total_amount: Total DN amount
        currency: Currency code
        status: Current DN status
        received_by: User who received goods
        notes: Additional notes
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_po_id", "po_id"),
        Index("ix_delivery_notes_po_number", "po_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_receipt_date", "receipt_date"),
        Index("ix_delivery_notes_created_at", "created_at"),
    )

    # Basic Information
    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        doc="Unique delivery note number",
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to linked PO",
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="PO number for quick reference",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="External vendor identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the vendor",
    )
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date goods were received",
    )

    # Financial Information
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="DN subtotal",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total DN amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="received",
        doc="Current DN status",
    )
    is_accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether goods were accepted",
    )

    # Additional Information
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who received goods",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="JSON metadata for extensibility",
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
        doc="Source system (erp, manual, ocr)",
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
        foreign_keys="CrossRef.dn_id",
    )


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery Note Line item model.

    Attributes:
        dn_id: Parent delivery note ID
        line_number: Line item number
        description: Item description
        quantity: Delivered quantity
        accepted_qty: Quantity accepted
        rejected_qty: Quantity rejected
        unit_price: Price per unit (from PO)
        amount: Total line amount
        po_line_id: Reference to PO line
        status: Line status
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent delivery note ID",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    accepted_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity accepted",
    )
    rejected_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Quantity rejected",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit (from PO)",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )

    # Matching References
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to PO line",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="received",
        doc="Line status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        foreign_keys=[po_line_id],
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="dn_line",
        foreign_keys="InvoiceLine.dn_line_id",
    )


# Add JSONB import at runtime
from sqlalchemy.dialects.postgresql import JSONB

DeliveryNote.__table__.c.metadata = Base.metadata
DeliveryNoteLine.__table__.c.metadata = Base.metadata
