# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus, LineStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note / Goods Receipt Note model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_vendor_number", "vendor_number"),
        Index("ix_delivery_notes_po_number", "po_number"),
        Index("ix_delivery_notes_receipt_date", "receipt_date"),
        Index("ix_delivery_notes_status", "status"),
        UniqueConstraint("dn_number", name="uq_delivery_notes_dn_number"),
    )

    # Document reference fields
    dn_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Delivery note number",
    )
    po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Referenced PO number",
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Vendor name",
    )

    # DN dates
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Delivery note issue date",
    )
    receipt_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Goods receipt date",
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total DN amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        default=DocumentStatus.PENDING,
        nullable=False,
        comment="DN status",
    )

    # ERP reference
    erp_dn_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="External ERP DN ID",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, status={self.status})>"


class DeliveryNoteLine(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_line_number", "line_number"),
        Index("ix_dn_lines_sku", "sku"),
        Index("ix_dn_lines_status", "status"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
    )

    # Foreign key to delivery note
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line reference
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line item sequence number",
    )

    # Product/service info
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product SKU",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Delivered quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure",
    )

    # Pricing (for reference)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Unit price (for reference)",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Line total amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        default=LineStatus.OPEN,
        nullable=False,
        comment="Line status",
    )

    # Matched PO line reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        comment="Matched PO line ID",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
        back_populates="matched_delivery_lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line_number={self.line_number}, qty={self.quantity})>"
