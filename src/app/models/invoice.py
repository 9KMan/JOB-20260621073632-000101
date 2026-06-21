// src/app/models/invoice.py
"""Invoice models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    String,
    Numeric,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.match import Match

INVOICE_STATUS = Enum(
    "INVOICE_STATUS",
    [
        "DRAFT",
        "RECEIVED",
        "MATCHING",
        "MATCHED",
        "PENDING_REVIEW",
        "APPROVED",
        "REJECTED",
        "DISPUTED",
        "PAID",
        "CANCELLED",
    ],
)


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice model."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[INVOICE_STATUS] = mapped_column(
        SQLEnum(INVOICE_STATUS, name="invoice_status"),
        default=INVOICE_STATUS.DRAFT,
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    po_reference: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="invoice",
        foreign_keys="Match.invoice_id",
    )

    __table_args__ = (
        Index("ix_inv_supplier_status", "supplier_id", "status"),
        Index("ix_inv_invoice_date", "invoice_date"),
        Index("ix_inv_po_reference", "po_reference"),
    )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice Line Item model."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_il_invoice_id", "invoice_id"),
        Index("ix_il_product_code", "product_code"),
    )
