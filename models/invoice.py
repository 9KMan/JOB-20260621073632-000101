// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryMixin
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    pass


class Invoice(Base, UUIDPrimaryMixin, TimestampMixin, SoftDeleteMixin):
    """
    Invoice header record.

    In AP automation an invoice is the primary triggering document.
    The matching engine compares its lines against anchored POs
    and delivery notes.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_po_reference_id", "po_reference_id"),
    )

    # ── Vendor / Header Info ──────────────────────────────────────────────────
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    po_reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True, comment="ERP system reference"
    )

    # ── Matching State ─────────────────────────────────────────────────────────
    status: Mapped[InvoiceStatus] = mapped_column(
        String(30), nullable=False, default=InvoiceStatus.SUBMITTED, index=True
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Overall match confidence 0–100"
    )
    match_decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    match_decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    match_decision_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InvoiceLine(Base, UUIDPrimaryMixin, TimestampMixin):
    """
    Individual line item on an Invoice.

    Each line is matched independently against PO lines
    and delivery-note lines in the cascade layer.
    """

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
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000")
    )
    matched_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.0000")
    )
    match_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # ── Relationships ───────────────────────────────────────────────────────────
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["POLine | None"] = relationship("POLine", back_populates="invoice_lines")
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="invoice_line_dn_lines",
        back_populates="invoice_lines",
        lazy="selectin",
    )


# ── Junction Table: InvoiceLine ↔ DeliveryNoteLine ─────────────────────────────

from sqlalchemy import Table, Column, ForeignKey
from models.base import Base as _Base

invoice_line_dn_lines = Table(
    "invoice_line_dn_lines",
    _Base.metadata,
    Column(
        "invoice_line_id",
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "delivery_note_line_id",
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
