// src/models/document.py
"""Document models for PO, Invoice, and Delivery Note."""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric, Date, DateTime, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DocumentStatus(str, enum.Enum):
    """Document status enumeration."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    CONFIRMED = "CONFIRMED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class DocumentType(str, enum.Enum):
    """Document type enumeration."""

    PURCHASE_ORDER = "PURCHASE_ORDER"
    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"


class PurchaseOrder(Base, TimestampMixin):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string

    # Relationships
    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_invoices: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        foreign_keys="MatchResult.po_id",
        back_populates="purchase_order",
    )
    matched_delivery_notes: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        foreign_keys="MatchResult.delivery_note_id",
        back_populates="delivery_note",
    )

    __table_args__ = (
        Index("ix_purchase_orders_supplier_status", "supplier_id", "status"),
    )


class POLine(Base, TimestampMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "po_lines"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    po_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )


class Invoice(Base, TimestampMixin):
    """Invoice model."""

    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="invoice",
    )

    __table_args__ = (
        Index("ix_invoices_supplier_status", "supplier_id", "status"),
        Index("ix_invoices_po_id", "po_id"),
    )


class InvoiceLine(Base, TimestampMixin):
    """Invoice Line Item model."""

    __tablename__ = "invoice_lines"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )


class DeliveryNote(Base, TimestampMixin):
    """Delivery Note model."""

    __tablename__ = "delivery_notes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="delivery_note",
    )

    __table_args__ = (
        Index("ix_delivery_notes_supplier_status", "supplier_id", "status"),
        Index("ix_delivery_notes_po_id", "po_id"),
    )


class DeliveryNoteLine(Base, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    delivery_note_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
