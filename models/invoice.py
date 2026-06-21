# models/invoice.py
"""Invoice and invoice line models."""
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
from models.enums import InvoiceStatus, LineType


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_created_at", "created_at"),
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

    # Invoice details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    invoice_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # ISO date format YYYY-MM-DD
    due_date: Mapped[Optional[str]] = mapped_column(
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

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50),
        nullable=False,
        default=InvoiceStatus.PENDING,
    )
    matched_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )  # ISO datetime
    approved_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )

    # Payment reference
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    paid_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )

    # Metadata
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )
    source_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_records: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="invoice",
        foreign_keys="MatchRecord.invoice_id",
    )
    exceptions: Mapped[List["MatchingException"]] = relationship(
        "MatchingException",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
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

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_received: Mapped[Decimal] = mapped_column(
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

    # Matching
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    match_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )


# Import MatchRecord here to avoid circular imports
class MatchRecord(Base, UUIDMixin, TimestampMixin):
    """Match record linking invoice to PO/DN."""

    __tablename__ = "match_records"
    __table_args__ = (
        Index("ix_match_records_invoice_id", "invoice_id"),
        Index("ix_match_records_po_id", "po_id"),
        Index("ix_match_records_status", "status"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scoring
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    price_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    quantity_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    delivery_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Decision
    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    # Timestamps
    matched_at: Mapped[str] = mapped_column(
        String(19),
        nullable=False,
    )
    confirmed_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )
    confirmed_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Match type
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="standard",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="match_records",
        foreign_keys=[invoice_id],
    )


# Import MatchingException
class MatchingException(Base, UUIDMixin, TimestampMixin):
    """Matching exception record."""

    __tablename__ = "matching_exceptions"
    __table_args__ = (
        Index("ix_matching_exceptions_invoice_id", "invoice_id"),
        Index("ix_matching_exceptions_type", "exception_type"),
        Index("ix_matching_exceptions_status", "status"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_records.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Exception details
    exception_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )

    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Variance amounts
    price_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    quantity_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    variance_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 4),
        nullable=True,
    )

    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    resolved_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="exceptions",
    )
