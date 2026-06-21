# models/invoice.py
"""Invoice and invoice line models."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import Currency, InvoiceStatus, LineType


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"

    # Vendor Information
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default=InvoiceStatus.PENDING.value, 
        nullable=False,
        index=True
    )
    
    # Reference
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Matching
    match_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ERP Reference
    erp_invoice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
        lazy="selectin",
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="invoices",
        lazy="selectin",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoices_status_date", "status", "invoice_date"),
        Index("ix_invoices_vendor_date", "vendor_code", "invoice_date"),
    )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    line_type: Mapped[str] = mapped_column(String(20), default=LineType.STANDARD.value, nullable=False)
    
    # Quantities
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    
    # Reference to PO Line
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Delivery Note Line Reference
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Matching
    match_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # ERP Reference
    erp_line_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    delivery_note_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_number", "invoice_id", "line_number"),
    )


from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.balance_ledger import BalanceLedger
