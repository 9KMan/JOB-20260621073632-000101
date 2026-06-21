# models/invoice.py
"""Invoice model and line items."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNoteLine
    from models.purchase_order import POLine


class Invoice(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)

    # Matching fields
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    decision_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ERP reference
    erp_invoice_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_system: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)

    # Additional metadata stored as JSON
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_code", "invoice_date"),
        Index("ix_invoices_status_created", "status", "created_at"),
        {"schema": None},
    )


class InvoiceLine(Base, UUIDPrimaryKey):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Matching fields
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    match_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Additional data
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["POLine | None"] = relationship("POLine", back_populates="invoice_lines")
    delivery_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine", back_populates="invoice_lines"
    )

    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line_number"),
        Index("ix_invoice_lines_po", "po_line_id"),
        Index("ix_invoice_lines_delivery", "delivery_line_id"),
    )
