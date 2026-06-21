# models/delivery_note.py
"""Delivery Note model for the AP Automation Engine."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


# Junction tables for many-to-many relationships
class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model from warehouse/ERP.

    Attributes:
        dn_number: Unique delivery note number
        vendor_id: External vendor identifier
        vendor_name: Supplier name
        po_reference: Reference to related PO
        invoice_reference: Reference to related invoice
        delivery_date: Date of delivery
        received_by: Person who received goods
        currency: Currency code
        total_amount: Total delivery amount
        status: Current document status
        notes: Additional notes
        metadata: JSON metadata for extensibility
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
    )

    # Basic DN information
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # References
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    invoice_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.PENDING,
    )

    # Additional fields
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
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
        return f"<DeliveryNote {self.dn_number} ({self.status.value})>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note line item model.

    Attributes:
        delivery_note_id: Parent delivery note reference
        line_number: Line item number
        description: Item description
        sku: Product SKU
        quantity: Delivered quantity
        unit_of_measure: UOM
        unit_price: Price per unit
        total_price: Line total
        condition: Goods condition (good, damaged, etc.)
        notes: Line notes
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_sku", "sku"),
    )

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Prices
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Condition
    condition: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        secondary="po_delivery_note_links",
        back_populates="delivery_note_lines",
        lazy="selectin",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        secondary="invoice_delivery_note_links",
        back_populates="delivery_note_lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"


# Junction table for PO to DN links
po_delivery_note_links = Table(
    "po_delivery_note_links",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "purchase_order_line_id",
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "delivery_note_line_id",
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("matched_quantity", Numeric(15, 4), nullable=False, default=Decimal("0.0000")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

# Junction table for Invoice to DN links
invoice_delivery_note_links = Table(
    "invoice_delivery_note_links",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "invoice_line_id",
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "delivery_note_line_id",
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("matched_quantity", Numeric(15, 4), nullable=False, default=Decimal("0.0000")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

from sqlalchemy import func
