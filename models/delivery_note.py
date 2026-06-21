# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models.

Represents delivery notes/receiving documents for goods received,
used in the 3-way match process with POs and invoices.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Enum,
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
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.cross_ref import CrossRef


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model representing goods received.

    Attributes:
        dn_number: Unique delivery note identifier
        supplier_id: External supplier identifier
        supplier_name: Supplier company name
        po_reference: Reference to original PO
        delivery_date: Date goods were delivered
        received_by: Person who received the goods
        status: Current delivery note status
        notes: Optional notes/comments
    """

    __tablename__ = "delivery_notes"

    # DN identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Reference
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_orders.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        Enum(DeliveryNoteStatus, name="dn_status"),
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
        index=True,
    )

    # Metadata
    received_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    vehicle_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    batch_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dn_supplier_date", "supplier_id", "delivery_date"),
        Index("ix_dn_status_date", "status", "delivery_date"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.supplier_name}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Individual line items on a delivery note.

    Attributes:
        line_number: Line item sequence number
        sku: Product/item SKU
        description: Item description
        quantity: Delivered quantity
        accepted_quantity: Quantity accepted (may differ if damaged)
        status: Current line status
    """

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "delivery_notes.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
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
        default=Decimal("0.0000"),
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="dn_line_status"),
        nullable=False,
        default=LineStatus.PENDING,
    )

    # Match confidence score (0-100)
    match_score: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="dn_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_dn_line_dn_line_num", "delivery_note_id", "line_number"),
        Index("ix_dn_line_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def has_shortage(self) -> bool:
        """Check if there's a shortage."""
        return self.accepted_quantity < self.quantity

    @property
    def has_surplus(self) -> bool:
        """Check if there's a surplus."""
        return self.accepted_quantity > self.quantity
