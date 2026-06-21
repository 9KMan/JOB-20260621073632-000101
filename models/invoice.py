# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatusType


class Invoice(Base, UUIDMixin, TimestampMixin):
    """AP Invoice header record.

    Represents a supplier invoice received for goods/services.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_code", "vendor_code"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_received_date", "received_date"),
        UniqueConstraint("vendor_code", "invoice_number", name="uq_vendor_invoice"),
    )

    # ── Header Fields ────────────────────────────────────────────────────────

    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Currency (ISO 4217)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, index=True
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0")
    )

    # Dates
    invoice_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Status & Workflow
    status: Mapped[InvoiceStatusType] = mapped_column(
        InvoiceStatusType,
        default=InvoiceStatusType.RECEIVED,
        nullable=False,
    )
    match_decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Reference to matched PO
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[matched_po_id],
        back_populates="matched_invoices",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_urls: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(500)), nullable=True
    )
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Lines ─────────────────────────────────────────────────────────────────

    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} vendor={self.vendor_code} status={self.status}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Line item on an Invoice."""

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
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Matched PO Line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_line: Mapped["POLine | None"] = relationship(
        "POLine",
        foreign_keys=[po_line_id],
        back_populates="matched_invoice_lines",
    )

    # Match metadata
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} qty={self.quantity}>"
