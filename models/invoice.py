# models/invoice.py
"""Invoice model definition."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus, MatchStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote
    from models.purchase_order import PurchaseOrderLine


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing a supplier invoice."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoice_vendor_number", "vendor_number"),
        Index("ix_invoice_invoice_number", "invoice_number"),
        Index("ix_invoice_status", "status"),
        Index("ix_invoice_invoice_date", "invoice_date"),
        Index("ix_invoice_match_status", "match_status"),
        {"schema": None},
    )

    # Header fields
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
    )

    # Amount fields
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Reference fields
    purchase_order_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_note_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Matching results
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Additional metadata
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Approved/rejected
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        foreign_keys="CrossRef.invoice_id",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.vendor_number}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_line_invoice_id", "invoice_id"),
        Index("ix_invoice_line_line_number", "line_number"),
    )

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Reference to PO line
    purchase_order_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match info
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0"))
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_line",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"
