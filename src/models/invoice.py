// src/models/invoice.py
"""Invoice models."""
from decimal import Decimal

from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    """Invoice status."""
    DRAFT = "draft"
    RECEIVED = "received"
    MATCHED = "matched"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Invoice(BaseModel):
    """Invoice header."""

    __tablename__ = "invoices"

    invoice_number = Column(String(100), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    po_reference = Column(String(50), nullable=True, index=True)  # Reference to PO number
    status = Column(Integer, default=InvoiceStatus.RECEIVED.value, nullable=False, index=True)
    invoice_date = Column(Text, nullable=False)  # ISO date string
    due_date = Column(Text, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_id = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    lines = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_records = relationship(
        "MatchRecord",
        foreign_keys="MatchRecord.invoice_id",
        back_populates="invoice",
        lazy="dynamic",
    )


class InvoiceLine(BaseModel):
    """Invoice line item."""

    __tablename__ = "invoice_lines"

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True)
    dn_line_id = Column(UUID(as_uuid=True), ForeignKey("delivery_note_lines.id"), nullable=True)
    item_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    line_total = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_rate = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    po_line = relationship("PurchaseOrderLine")
    dn_line = relationship("DeliveryNoteLine")
