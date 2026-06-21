# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, Timestamps, UUIDPrimaryKey
from models.enums import ApprovalDecision, InvoiceStatus, MatchConfidence


class Invoice(Base, UUIDPrimaryKey, Timestamps):
    """Top-level invoice entity."""

    __tablename__ = "invoices"

    # ── Vendor ─────────────────────────────────────────────────────────────
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Reference fields ────────────────────────────────────────────────────
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Amounts ──────────────────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        index=True,
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    # ── Status ──────────────────────────────────────────────────────────────
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # ── Matching results ─────────────────────────────────────────────────────
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    match_confidence: Mapped[MatchConfidence | None] = mapped_column(
        Enum(MatchConfidence, name="match_confidence"),
        nullable=True,
    )
    approval_decision: Mapped[ApprovalDecision | None] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision"),
        nullable=True,
    )
    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── ERP / raw data ──────────────────────────────────────────────────────
    erp_invoice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_code", "invoice_date"),
        Index("ix_invoices_status_match_score", "status", "match_score"),
    )


class InvoiceLine(Base, UUIDPrimaryKey, Timestamps):
    """Line-level detail for an invoice."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Product / SKU ───────────────────────────────────────────────────────
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Quantities & amounts ────────────────────────────────────────────────
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # ── Matching fields ─────────────────────────────────────────────────────
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────────
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_id_number", "invoice_id", "line_number"),
    )


# ── Forward reference resolution ──────────────────────────────────────────────
from models.purchase_order import PurchaseOrderLine  # noqa: E402, F401
