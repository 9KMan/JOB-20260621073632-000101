# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


# Association table for many-to-many between DeliveryNoteLine and InvoiceLine
delivery_note_invoice_lines = Table(
    "delivery_note_invoice_lines",
    Base.metadata,
    Column(
        "delivery_note_line_id",
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "invoice_line_id",
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note header model.

    Represents a delivery note (goods receipt) from a vendor.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_dn_number", "dn_number"),
        Index("ix_dn_vendor_number", "vendor_number"),
        Index("ix_dn_po_id", "po_id"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_delivery_date", "delivery_date"),
        Index("ix_dn_created_at", "created_at"),
        {"schema": None},
    )

    # Delivery Note identification
    dn_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Reference to PO
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
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

    # Financials
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status tracking
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(30),
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
        index=True,
    )

    # Invoicing tracking
    is_fully_invoiced: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Metadata
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    raw_data: Mapped[dict | None] = mapped_column(
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
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.vendor_number}>"


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Delivery Note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_line_number", "line_number"),
        Index("ix_dn_lines_product_number", "product_number"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
        Index("ix_dn_lines_status", "status"),
        UniqueConstraint("dn_id", "line_number", name="uq_dn_line_number"),
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
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product identification
    product_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LineStatus.OPEN,
        index=True,
    )

    # PO Line reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Invoice Line references (many-to-many)
    invoice_line_ids: Mapped[list[uuid.UUID]] = mapped_column(
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
        lazy="selectin",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        lazy="selectin",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        secondary="delivery_note_invoice_lines",
        back_populates="delivery_note_lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        total_invoiced = sum(
            il.quantity_invoiced for il in self.invoice_lines
        )
        return total_invoiced >= self.quantity_delivered
