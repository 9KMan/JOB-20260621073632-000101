# models/delivery_note.py
"""
DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes/receiving documents that provide
evidence of goods received, used in three-way matching.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.cross_ref import CrossRef


class DeliveryNote(Base):
    """
    Delivery Note header model.
    
    Represents a delivery note or goods receiving document
    that provides evidence of goods received.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dns_supplier_number", "supplier_number"),
        Index("ix_dns_dn_number", "dn_number"),
        Index("ix_dns_po_reference", "po_reference"),
        Index("ix_dns_status", "status"),
        Index("ix_dns_delivery_date", "delivery_date"),
        Index("ix_dns_created_at", "created_at"),
        UniqueConstraint("supplier_number", "dn_number", name="uq_dn_supplier_number"),
        {"schema": None},
    )

    # DN identification
    supplier_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Supplier/Vendor ID in the ERP system",
    )

    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Supplier/Vendor number",
    )

    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Supplier/Vendor name",
    )

    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Delivery note number",
    )

    # PO reference
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Reference to original PO number",
    )

    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Linked PO ID",
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date of delivery",
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Total delivery note amount",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.RECEIVED,
        index=True,
        comment="Current delivery note status",
    )

    # Source system
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Source system identifier",
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Original reference in source system",
    )

    # Receiving information
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Person who received the goods",
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Receiving timestamp",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes",
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional metadata as JSON",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
        foreign_keys="CrossRef.delivery_note_id",
        cascade="all, delete-orphan",
    )

    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="balance_entries",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} from {self.supplier_number}>"


class DeliveryNoteLine(Base):
    """
    Delivery Note line item model.
    
    Represents individual line items on a delivery note
    that can be matched against PO and invoice lines.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_line_number", "line_number"),
        Index("ix_dn_lines_product_code", "product_code"),
        {"schema": None},
    )

    # Parent reference
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Line item number on the delivery note",
    )

    # Product information
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product/SKU code",
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Line item description",
    )

    # Quantities
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity delivered",
    )

    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity accepted",
    )

    rejected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity rejected",
    )

    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Unit price",
    )

    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Line total",
    )

    # PO line reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Linked PO line ID",
    )

    # Matching state
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity matched to invoices",
    )

    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Amount matched",
    )

    # Relationship
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.product_code} x {self.delivered_quantity}>"

    @property
    def is_fully_matched(self) -> bool:
        """Check if line is fully matched."""
        return self.matched_quantity >= self.accepted_quantity

    @property
    def unmatched_quantity(self) -> Decimal:
        """Calculate unmatched quantity."""
        return self.accepted_quantity - self.matched_quantity

    @property
    def match_percentage(self) -> float:
        """Calculate match percentage for this line."""
        if self.accepted_quantity == 0:
            return 100.0
        return float((self.matched_quantity / self.accepted_quantity) * 100)
