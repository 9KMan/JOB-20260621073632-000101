# app/models/invoice.py
"""Invoice and Invoice Line models."""
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class InvoiceStatus(str, enum.Enum):
    """Invoice status enum."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHED = "matched"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(Base, TimestampMixin):
    """Invoice model received from vendors."""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    vendor_invoice_number = Column(String(100), nullable=True, index=True)
    po_reference = Column(String(50), nullable=True, index=True)
    status = Column(String(20), default=InvoiceStatus.SUBMITTED.value, nullable=False, index=True)
    invoice_date = Column(String(20), nullable=False)  # ISO date string
    due_date = Column(String(20), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    shipping_cost = Column(Numeric(15, 2), default=0, nullable=False)
    amount_paid = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)  # Original extracted data

    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")
    lines = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matching_results = relationship(
        "MatchingResult",
        foreign_keys="MatchingResult.invoice_id",
        back_populates="invoice",
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, total={self.total_amount})>"


class InvoiceLine(Base, TimestampMixin):
    """Invoice Line Item model."""

    __tablename__ = "invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 4), default=0, nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), default=0, nullable=False)
    line_total = Column(Numeric(15, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    match_line_results = relationship("MatchLineResult", back_populates="invoice_line")

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line_number={self.line_number}, product={self.product_code})>"

    def calculate_line_total(self) -> None:
        """Calculate line total including tax."""
        self.line_total = (self.quantity * self.unit_price) * (1 + self.tax_rate)
