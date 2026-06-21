# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    invoice_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="standard",
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        nullable=True,
    )
    is_credit_memo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    external_ref: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_created", "status", "created_at"),
    )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    po_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number", unique=True),
        Index("ix_invoice_lines_po_line", "po_line_id"),
    )
