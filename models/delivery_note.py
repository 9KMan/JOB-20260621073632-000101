// models/delivery_note.py
"""Delivery Note model for the AP Automation Engine."""

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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CustomMixin, SoftDeleteMixin
from models.enums import DocumentStatus, MatchStatus

if TYPE_CHECKING:
    from models.cross_ref import CrossRef
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrder


class DeliveryNote(Base, CustomMixin, SoftDeleteMixin):
    """Delivery Note model.

    Attributes:
        dn_number: Unique DN number.
        vendor_id: External vendor identifier.
        vendor_name: Vendor name for display.
        po_id: Related PO ID (optional).
        po_number: Related PO number for display.
        delivery_date: Date of delivery.
        received_date: Date goods were received.
        status: Current document status.
        match_status: Current matching status.
        total_amount: Total DN amount.
        currency: ISO currency code.
        delivered_by: Carrier/supplier delivering.
        received_by: Person who received goods.
        notes: Additional notes.
        is_partial: Whether this is a partial delivery.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_vendor_id", "vendor_id"),
        Index("ix_dn_po_id", "po_id"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_match_status", "match_status"),
        Index("ix_dn_delivery_date", "delivery_date"),
        Index("ix_dn_created_at", "created_at"),
        {"schema": None},
    )

    # Core DN fields
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Status fields
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        default=DocumentStatus.SUBMITTED,
        nullable=False,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        String(20),
        default=MatchStatus.PENDING,
        nullable=False,
    )

    # Financial fields
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Additional fields
    delivered_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    received_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_partial: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Relationships
    dn_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
        foreign_keys=[po_id],
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="delivery_note",
        foreign_keys="CrossRef.delivery_note_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.total_amount} {self.currency}>"


class DeliveryNoteLine(Base, CustomMixin):
    """Delivery Note line item model.

    Attributes:
        dn_id: Parent DN ID.
        line_number: Line item number.
        description: Line description.
        quantity: Delivered quantity.
        unit: Unit of measure.
        po_line_id: Reference to matched PO line (optional).
        invoice_line_id: Reference to matched invoice line (optional).
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_line_dn_id", "dn_id"),
        {"schema": None},
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="dn_lines",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.quantity} {self.unit}>"
