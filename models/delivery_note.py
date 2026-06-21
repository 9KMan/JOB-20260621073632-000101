# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes from suppliers or internal systems.
"""

import uuid
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

from models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from models.enums import DeliveryNoteStatus, LineStatus


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model.
    
    Represents goods received against a PO.
    """
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_vendor_number", "vendor_number"),
        Index("ix_dn_dn_number", "dn_number"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_dn_date", "dn_date"),
        Index("ix_dn_po_id", "po_id"),
        {"schema": None},
    )
    
    # External references
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # DN identification
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    carrier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # References
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Dates
    dn_date: Mapped[Date] = mapped_column(Date, nullable=False)
    received_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    # Financial
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.CONFIRMED,
        index=True,
    )
    
    # Shipping details
    ship_to_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    received_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Source
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="warehouse")
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.status.value}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note line item model.
    
    Each delivery note can have multiple line items.
    """
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_item_number", "item_number"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
        {"schema": None},
    )
    
    # Foreign key to parent delivery note
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line details
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Product identification
    item_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    
    # Pricing (for matching purposes)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    line_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.OPEN,
    )
    
    # Matching reference
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Match tracking
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    
    # Acceptance notes
    acceptance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"
