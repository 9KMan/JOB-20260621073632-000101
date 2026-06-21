# src/models/invoice.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.matching import MatchingResult, MatchingLine


class Invoice(BaseModel):
    """
    Invoice model for AP matching.
    """
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoice_supplier_invoice_number", "supplier_id", "invoice_number", unique=True),
        Index("ix_invoice_supplier_id", "supplier_id"),
        Index("ix_invoice_status", "status"),
        Index("ix_invoice_invoice_date", "invoice_date"),
    )

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    matched_pos: Mapped[list["MatchingResult"]] = relationship(
        "MatchingResult",
        back_populates="invoice",
        foreign_keys="MatchingResult.invoice_id"
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, supplier={self.supplier_id})>"


class InvoiceLine(BaseModel):
    """
    Individual line items in an Invoice.
    """
    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_il_invoice_id", "invoice_id"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False
    )
    
    line_number: Mapped[int] = mapped_column(nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    tax_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines"
    )
    matching_lines: Mapped[list["MatchingLine"]] = relationship(
        "MatchingLine",
        back_populates="invoice_line"
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line_number={self.line_number}, item={self.item_code})>"
