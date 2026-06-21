# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Invoice header model."""

    __tablename__ = "invoices"

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    posting_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status and Matching
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True,
    )
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Reference
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        nullable=True,
    )

    # Exception
    has_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exception_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exception_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Approval
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft Delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="invoices",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_match", "status", "match_decision"),
    )


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"

    # Parent
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/Service Reference
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Matching
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Match scores
    price_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    qty_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    overall_match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Exception
    has_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exception_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    matched_po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[matched_po_line_id],
    )
    matched_dn_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        foreign_keys=[matched_dn_line_id],
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number"),
    )
