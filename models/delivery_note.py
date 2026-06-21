# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from models.base import Base, CompanyMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DeliveryNoteStatus, LineType

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrder


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyMixin):
    """Delivery Note database model.

    Represents a delivery note (DN/GRN) received from a supplier,
    documenting goods delivered for matching with POs and invoices.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        UniqueConstraint("dn_number", "company_code", name="uq_dn_number_company"),
        Index("ix_delivery_notes_supplier_code", "supplier_code"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
        Index("ix_delivery_notes_po_id", "po_id"),
        {"schema": None},
    )

    # Reference fields
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Supplier information
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Date fields
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial fields
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DeliveryNoteStatus.CREATED.value,
        index=True,
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    carrier: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    tracking_number: Mapped[str | None] = mapped_column(
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
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.total_amount} {self.currency}>"

    @property
    def is_received(self) -> bool:
        """Check if DN has been received."""
        return self.status in [
            DeliveryNoteStatus.RECEIVED.value,
            DeliveryNoteStatus.PARTIAL.value,
            DeliveryNoteStatus.COMPLETE.value,
        ]


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery Note Line Item database model.

    Represents individual line items on a delivery note for line-level
    matching against PO lines and invoice lines.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_sku", "sku"),
        {"schema": None},
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    external_line_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Product/Service identification
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    line_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=LineType.STANDARD.value,
    )

    # Quantity delivered
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Matching
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def is_fully_received(self) -> bool:
        """Check if line is fully received."""
        return self.quantity_received >= self.quantity_delivered

    @property
    def received_percentage(self) -> float:
        """Calculate received percentage."""
        if self.quantity_delivered == 0:
            return 100.0
        return float(self.quantity_received / self.quantity_delivered * 100)
