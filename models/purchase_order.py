# models/purchase_order.py
"""Purchase order and line models."""
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import LineType, PurchaseOrderStatus


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order header model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_created_at", "created_at"),
    )

    # Vendor information
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    vendor_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # PO details
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    po_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # ISO date format
    expected_delivery_date: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.ACTIVE,
    )

    # Metadata
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="erp",
    )
    source_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    terms: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        foreign_keys="DeliveryNote.purchase_order_id",
    )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase order line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "po_id", "line_number"),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    line_type: Mapped[LineType] = mapped_column(
        String(20),
        nullable=False,
        default=LineType.STANDARD,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product/SKU info
    product_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    product_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    extended_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Tax
    tax_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Delivery schedule
    promised_date: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    expected_date: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Receipt tracking
    is_fully_received: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    receipt_date: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
    )
    delivery_note_lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys="DeliveryNoteLine.po_line_id",
    )


# Add forward reference for InvoiceLine
from models.invoice import InvoiceLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery note header model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_dn_number", "dn_number", unique=True),
        Index("ix_delivery_notes_status", "status"),
    )

    # Vendor information
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    vendor_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Purchase order reference
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # DN details
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    dn_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    received_date: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="confirmed",
    )

    # Metadata
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="warehouse",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
        foreign_keys=[purchase_order_id],
    )
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery note line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
    )

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product info
    product_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
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

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        foreign_keys=[po_line_id],
    )
    invoice_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
        foreign_keys="InvoiceLine.delivery_note_line_id",
    )
