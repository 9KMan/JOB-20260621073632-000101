// models/delivery_note.py
"""Delivery Note model definition.

This module defines the DeliveryNote and DeliveryNoteLine SQLAlchemy models
with their relationships and methods.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import DeliveryNoteStatus, LineStatus


class DeliveryNote(Base):
    """Delivery Note database model.

    Represents a delivery note from the vendor or logistics system.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_po_number", "po_number"),
        Index("ix_delivery_notes_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # DN identification
    dn_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    po_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # DN dates
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.ISSUED.value,
        index=True,
    )

    # Reference to source system
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"

    @property
    def is_processed(self) -> bool:
        """Check if DN has been fully processed."""
        return self.status == DeliveryNoteStatus.PROCESSED.value


class DeliveryNoteLine(Base):
    """Delivery Note Line Item model.

    Represents individual line items within a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "dn_id", "line_number"),
        Index("ix_delivery_note_lines_product_code", "product_code"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Parent reference
    dn_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product identification
    product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.OPEN.value,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def remaining_to_receive(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.quantity_delivered - self.quantity_received

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity that can be invoiced."""
        return self.quantity_received - self.quantity_invoiced
