// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes from suppliers or OCR processing.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery note model.

    Represents goods received or services rendered.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_created_at", "created_at"),
        UniqueConstraint("vendor_id", "dn_number", name="uq_vendor_dn"),
    )

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor display name",
    )

    # Delivery Note Details
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Delivery note number",
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Associated purchase order number",
    )
    delivery_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Delivery date (YYYY-MM-DD)",
    )
    received_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Goods receipt date (YYYY-MM-DD)",
    )

    # Reference
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="External reference number",
    )
    carrier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Carrier/shipping company",
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Tracking number",
    )

    # Financial Information
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total delivery note amount",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.CONFIRMED.value,
        index=True,
        doc="Current delivery note status",
    )

    # Source Information
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="erp",
        doc="Source system (erp, ocr, manual)",
    )
    ocr_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="OCR confidence score if from OCR",
    )

    # Additional Fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # Relationships
    po_reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        doc="Referenced purchase order ID",
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_dn",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} from {self.vendor_id}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Individual line item on a delivery note."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "delivery_note_id"),
        Index("ix_dn_lines_line_number", "delivery_note_id", "line_number"),
        Index("ix_dn_lines_sku", "sku"),
    )

    # Foreign Key
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent delivery note ID",
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )

    # Product Information
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU/UPC",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Internal product code",
    )
    barcode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product barcode",
    )

    # Quantity
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    quantity_accepted: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Accepted quantity (after inspection)",
    )
    quantity_rejected: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Rejected quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Reference to PO Line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched purchase order line ID",
    )

    # Batch/Lot Information
    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Batch/lot number",
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Serial number",
    )
    expiry_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Expiry date (YYYY-MM-DD)",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.sku or 'No SKU'}>"
