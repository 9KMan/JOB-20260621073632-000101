// src/models/invoice.py
"""Invoice models."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.models.base import Base, BaseModel


class Invoice(Base, BaseModel):
    """Invoice model."""
    __tablename__ = "invoices"

    invoice_number = Column(String(50), nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    # Reference to PO
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    po_number = Column(String(50), nullable=True, index=True)
    
    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    receipt_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, matched, approved, rejected, paid
    currency = Column(String(3), default="USD", nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Matching info
    match_score = Column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000
    match_status = Column(String(50), nullable=True)  # confirmed, pending, rejected
    
    # Notes
    notes = Column(Text, nullable=True)
    payment_terms = Column(String(255), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Metadata
    received_by = Column(String(36), nullable=True)
    matched_by = Column(String(36), nullable=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    lines: List["InvoiceLine"] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    po: Optional["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    match_results: List["MatchResult"] = relationship(
        "MatchResult",
        foreign_keys="MatchResult.invoice_id",
        back_populates="invoice",
        lazy="selectin",
    )
    balance_entries: List["BalanceLedger"] = relationship(
        "BalanceLedger",
        foreign_keys="BalanceLedger.invoice_id",
        back_populates="invoice",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(Base, BaseModel):
    """Invoice Line model."""
    __tablename__ = "invoice_lines"

    invoice_id = Column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=True, index=True)
    item_description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Reference to PO line
    po_line_id = Column(String(36), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    dn_line_id = Column(String(36), ForeignKey("delivery_note_lines.id", ondelete="SET NULL"), nullable=True)
    
    # Match info
    match_score = Column(Numeric(5, 4), nullable=True)

    # Relationships
    invoice: "Invoice" = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Optional["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    dn_line: Optional["DeliveryNoteLine"] = relationship(
        "DeliveryNoteLine",
        foreign_keys=[dn_line_id],
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}>"
