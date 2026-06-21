// src/models/invoice.py
"""Invoice and Invoice Line models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Date, DateTime, Numeric, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, BaseModel

if TYPE_CHECKING:
    from src.models.vendor import Vendor
    from src.models.match import Match
    from src.models.balance import Balance


class Invoice(Base, BaseModel):
    """Invoice model received from vendors."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    po_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    attachments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        back_populates="invoices"
    )
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="invoice"
    )
    balances: Mapped[list["Balance"]] = relationship(
        "Balance",
        back_populates="invoice"
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"


class InvoiceLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Invoice Line item model."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    item_code: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, item={self.item_code}, qty={self.quantity})>"


# Import func for server_default
from sqlalchemy import func
