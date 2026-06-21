// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model.

    Represents delivery notes/confirmation of delivery from suppliers.

    Attributes:
        id: UUID primary key
        dn_number: Unique delivery note number
        supplier_id: External supplier identifier
        supplier_name: Name of the supplier
        dn_date: Date of the delivery note
        delivery_date: Actual/scheduled delivery date
        purchase_order_id: Reference to related PO
        status: Current DN status
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        UniqueConstraint("dn_number", "supplier_id", name="uq_dn_number_supplier"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_supplier_id", "supplier_id"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_po_id", "purchase_order_id"),
        {"schema": None},
    )

    # Core fields
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Unique delivery note number",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="External supplier identifier",
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the supplier",
    )

    # Dates
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date of the delivery note",
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Actual/scheduled delivery date",
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were received",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
        index=True,
        doc="Current DN status",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments",
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether all items have been received",
    )

    # Reference to PO
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to related purchase order",
    )

    # Relations
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model.

    Represents individual line items on a delivery note.

    Attributes:
        id: UUID primary key
        delivery_note_id: Parent DN reference
        line_number: Line item number
        sku: Product SKU or item code
        description: Item description
        quantity: Delivered quantity
        purchase_order_line_id: Reference to matched PO line
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
        Index("ix_delivery_note_lines_po_line_id", "purchase_order_line_id"),
        Index("ix_delivery_note_lines_sku", "sku"),
        {"schema": None},
    )

    # Foreign key
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent delivery note reference",
    )

    # Line item details
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number on the DN",
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU or item code",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        doc="Delivered quantity",
    )
    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        default=Decimal("0"),
        doc="Accepted quantity (may differ if damaged)",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Matching references
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to matched purchase order line",
    )

    # Relations
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
