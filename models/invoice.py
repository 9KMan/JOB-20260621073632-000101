"""Invoice and InvoiceLine ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Header-level vendor invoice."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    received_at: Mapped[datetime] = mapped_column(nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        String(32), nullable=False, default=DocumentStatus.PENDING, index=True
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_ocr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_invoice_no", "vendor_id", "invoice_number", unique=True),
        Index("ix_invoices_status_invoice_date", "status", "invoice_date"),
    )


class InvoiceLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Line item on a vendor invoice."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="lines")

    __table_args__ = (
        Index("ux_invoice_lines_invoice_line_no", "invoice_id", "line_number", unique=True),
    )
