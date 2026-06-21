# models/invoice.py
"""Invoice model for AP Automation Core Engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import InvoiceStatus, MatchDecision

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrderLine
    from models.delivery_note import DeliveryNoteLine


class InvoiceLine(TimestampMixin, UUIDPrimaryKeyMixin, Base):
    """Individual line item on an invoice."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_line_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Product/Service info
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Matching info
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
    match_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_decision: Mapped[MatchDecision | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Tax info
    tax_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hsn_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
        Index("ix_invoice_lines_invoice_sku", "invoice_id", "sku"),
    )


class Invoice(TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin, Base):
    """Invoice model representing AP invoices to be matched.

    Invoices can be matched against Purchase Orders and Delivery Notes
    based on line items, pricing, and quantities.
    """

    __tablename__ = "invoices"

    # External reference
    external_invoice_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Supplier info
    supplier_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Invoice dates
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial info
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(15, 6),
        nullable=False,
        default=Decimal("1"),
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Discount info
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )
    is_credit_memo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Matching results
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_decision: Mapped[MatchDecision | None] = mapped_column(
        String(20),
        nullable=True,
    )
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Payment info
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Source info
    source_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number",
    )

    __table_args__ = (
        Index("ix_invoices_supplier_date", "supplier_id", "invoice_date"),
        Index("ix_invoices_status_date", "status", "invoice_date"),
        Index("ix_invoices_external", "source_system", "external_invoice_id"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.supplier_invoice_number} - {self.total_amount} {self.currency}>"


__all__ = ["Invoice", "InvoiceLine"]
