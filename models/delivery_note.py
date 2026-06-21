// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Delivery notes (or goods received notes) document the receipt of goods.
Each delivery note can have multiple line items.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import DeliveryNoteStatus, LineStatus


class DeliveryNote(Base):
    """Delivery Note model (also known as Goods Received Note).

    Represents a delivery note documenting receipt of goods from a vendor.

    Attributes:
        id: UUID primary key
        dn_number: Unique delivery note number
        vendor_id: External vendor identifier
        vendor_name: Vendor name for display
        delivery_date: Date goods were delivered
        status: Delivery note status
        total_amount: Total delivery value
        currency: Currency code
        lines: Associated line items
    """

    __tablename__ = "delivery_notes"

    # Document identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(),
        nullable=False,
    )

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # References
    external_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Receiving information
    received_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    warehouse_location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quality check
    quality_check_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    quality_check_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Additional data
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
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
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_note",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dn_vendor_date", "vendor_id", "delivery_date"),
        Index("ix_dn_status_date", "status", "delivery_date"),
        Index("ix_dn_po_reference", "purchase_order_id"),
        Index("ix_dn_po_number", "po_number"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.total_amount} {self.currency}>"


class DeliveryNoteLine(Base):
    """Delivery Note Line Item model.

    Represents individual line items on a delivery note.

    Attributes:
        id: UUID primary key
        delivery_note_id: Parent delivery note reference
        line_number: Line sequence number
        description: Item description
        quantity: Delivered quantity
        accepted_quantity: Quantity accepted after quality check
        unit_price: Price per unit
        total_amount: Line total
        sku: Product/Item SKU
        uom: Unit of measure
    """

    __tablename__ = "delivery_note_lines"

    # Parent reference
    delivery_note_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    rejected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Product reference
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    uom: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        default=LineStatus.OPEN,
        nullable=False,
        index=True,
    )

    # Match tracking
    matched_po_line_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Quality issues
    has_quality_issue: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    quality_issue_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Additional data
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    matched_po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )

    __table_args__ = (
        Index("ix_dn_line_dn", "delivery_note_id", "line_number"),
        Index("ix_dn_line_sku", "sku"),
        Index("ix_dn_line_matched_po", "matched_po_line_id"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.accepted_quantity
