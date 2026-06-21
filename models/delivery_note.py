# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

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
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import BaseModel
from models.enums import DeliveryNoteStatus, LineStatus


if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder


class DeliveryNote(BaseModel):
    """
    Delivery Note model for goods received.
    
    Attributes:
        dn_number: Unique DN number
        po_number: Reference PO number
        vendor_id: Vendor identifier
        vendor_name: Vendor name
        delivery_date: Date goods were delivered
        status: Current DN status
    """

    __tablename__ = "delivery_notes"

    # Core DN fields
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique delivery note number",
    )
    po_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Reference to PO number",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor identifier",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name",
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date goods were delivered",
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        doc="Date received in system",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="DN subtotal",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.SENT,
        index=True,
        doc="Current DN status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes",
    )

    # Source tracking
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="erp",
        doc="Source system (erp, ocr, manual)",
    )
    erp_dn_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="DN ID in ERP system",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_date", "vendor_id", "delivery_date"),
        Index("ix_delivery_notes_po_ref", "po_reference"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, number={self.dn_number}, status={self.status})>"


class DeliveryNoteLine(BaseModel):
    """
    Delivery Note Line Item model.
    
    Attributes:
        line_number: Line item number
        description: Line description
        quantity: Delivered quantity
        unit_price: Price per unit (from PO)
        line_total: Total line amount
        matched_po_line_id: Reference to matched PO line
        status: Line status
    """

    __tablename__ = "delivery_note_lines"

    # Parent reference
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to parent DN",
    )

    # Line details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number",
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Delivered quantity",
    )
    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Accepted quantity",
    )
    rejected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Rejected quantity",
    )

    # Amounts
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit from PO",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )

    # Match references
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched PO line",
    )
    match_score: Mapped[int | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Match score for this line",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        index=True,
        doc="Line status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Line-specific notes",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_line", "delivery_note_id", "line_number"),
        Index("ix_dn_lines_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line={self.line_number}, qty={self.quantity})>"
