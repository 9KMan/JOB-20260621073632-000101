// src/models/invoice.py
"""Invoice models."""
import decimal
import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel


class InvoiceStatus(str, Enum):
    """Invoice status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHING = "matching"
    MATCHED = "matched"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    PAID = "paid"
    CANCELLED = "cancelled"


class InvoiceMatchStatus(str, Enum):
    """Invoice matching status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    REJECTED = "rejected"


class Invoice(BaseModel):
    """Invoice model."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    tax_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=InvoiceStatus.DRAFT.value, nullable=False)
    match_status: Mapped[str] = mapped_column(
        String(20),
        default=InvoiceMatchStatus.PENDING.value,
        nullable=False,
    )
    match_confidence: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
    )
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="invoice",
    )

    __table_args__ = (
        Index("ix_invoices_supplier_status", "supplier_id", "status"),
        Index("ix_invoices_po_status", "purchase_order_id", "status"),
    )


class InvoiceLine(BaseModel):
    """Invoice Line Item model."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number", unique=True),
    )
