# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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

from models.base import Base, CommonMixin
from models.enums import (
    DeliveryNoteStatus,
    SourceSystem,
    get_delivery_note_status_enum,
    get_source_system_enum,
)

if TYPE_CHECKING:
    from models.cross_ref import CrossRef
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, CommonMixin):
    """Delivery Note model (also known as Goods Receipt Note)."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        UniqueConstraint("dn_number", "vendor_id", name="uq_dn_vendor"),
        Index("ix_dn_vendor_id", "vendor_id"),
        Index("ix_dn_dn_date", "dn_date"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_received_date", "received_date"),
        {"schema": None},
    )

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Delivery note details
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Delivery note number",
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date on delivery note",
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date goods were received",
    )
    carrier: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    tracking_number: Mapped[str | None] = mapped_column(
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
        String(100),
        nullable=True,
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        get_delivery_note_status_enum(),
        nullable=False,
        default=DeliveryNoteStatus.ISSUED,
        index=True,
    )

    # Source
    source_system: Mapped[SourceSystem] = mapped_column(
        get_source_system_enum(),
        nullable=False,
        default=SourceSystem.ERP,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Additional fields
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    warehouse: Mapped[str | None] = mapped_column(
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
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        foreign_keys="CrossRef.dn_id",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.vendor_id} - {self.status.value}>"


class DeliveryNoteLine(Base, CommonMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_line_dn_id", "delivery_note_id"),
        Index("ix_dn_line_po_line_id", "po_line_id"),
        {"schema": None},
    )

    # Parent DN
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Delivered quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Reference to PO line
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Product reference
    product_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Quality check
    accepted_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Quantity accepted after QC",
    )
    rejected_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Quantity rejected in QC",
    )
    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="dn_line",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def effective_quantity(self) -> Decimal:
        """Effective quantity (accepted after QC)."""
        return self.accepted_quantity if self.accepted_quantity is not None else self.quantity
