// models/delivery_note.py
"""
DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Delivery notes represent goods received from vendors.
They are used as intermediate evidence for invoice matching.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import (
    DeliveryNoteStatus,
    LineStatus,
    dn_status_enum,
    line_status_enum,
)

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.balance_ledger import BalanceLedger


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """
    Delivery Note header table.
    
    Represents a goods received note (GRN) or delivery advice.
    Links purchases to receipts for 3-way matching.
    """

    __tablename__ = "deliverynotes"

    # DN identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Delivery note number",
    )
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Vendor identifier code",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor display name",
    )

    # Date fields
    shipment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date goods were shipped",
    )
    receipt_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were received",
    )

    # Financial details
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="DN subtotal",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total DN amount",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO 4217 currency code",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        dn_status_enum,
        nullable=False,
        default=DeliveryNoteStatus.RECEIVED,
        index=True,
        doc="Current DN status",
    )

    # Reference fields
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Linked purchase order",
    )
    carrier_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Shipping carrier name",
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Shipment tracking number",
    )
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Person who received the goods",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="External system reference",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Delivery notes or comments",
    )

    # JSON metadata
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
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
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_note",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_dn_vendor_date", "vendor_code", "shipment_date"),
        Index("ix_dn_po", "purchase_order_id"),
        Index("ix_dn_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryNote(id={self.id}, "
            f"dn_number={self.dn_number}, "
            f"vendor={self.vendor_code})>"
        )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """
    Delivery Note Line item table.
    
    Represents individual line items on a delivery note.
    Used for line-level matching with POs and invoices.
    """

    __tablename__ = "deliverynote_lines"

    # Foreign key
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverynotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )

    # Product identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Product SKU",
    )
    gtin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Global Trade Item Number",
    )
    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Batch/lot number",
    )

    # Quantities
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Quantity delivered",
    )
    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Quantity accepted after inspection",
    )
    rejected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity rejected",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure code",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        line_status_enum,
        nullable=False,
        default=LineStatus.OPEN,
        doc="Line matching status",
    )

    # Matching
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="Matched purchase order line",
    )
    matched_invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="Matched invoice line",
    )

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    matched_po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_delivery_note_lines",
        foreign_keys=[matched_po_line_id],
    )
    matched_invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        foreign_keys=[matched_invoice_line_id],
    )

    __table_args__ = (
        Index("ix_dnl_dn_line", "delivery_note_id", "line_number"),
        Index("ix_dnl_sku", "sku"),
        Index("ix_dnl_po_line", "matched_po_line_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryNoteLine(id={self.id}, "
            f"dn={self.delivery_note_id}, "
            f"line={self.line_number}, "
            f"qty={self.delivered_quantity})>"
        )
