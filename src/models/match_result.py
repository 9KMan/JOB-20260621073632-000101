// src/models/match_result.py
"""Match Result models for 3-way matching."""
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.models.base import Base, BaseModel


class MatchResult(Base, BaseModel):
    """Match Result model - represents a 3-way match between PO, Invoice, and DN."""
    __tablename__ = "match_results"

    # Document references
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    dn_id = Column(String(36), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True, index=True)

    # Match scores
    overall_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)  # 0.0000 to 1.0000
    po_invoice_score = Column(Numeric(5, 4), nullable=True)
    po_dn_score = Column(Numeric(5, 4), nullable=True)
    invoice_dn_score = Column(Numeric(5, 4), nullable=True)
    
    # Amount comparison
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    amount_variance = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_variance_percent = Column(Numeric(8, 4), default=Decimal("0.0000"), nullable=False)
    
    # Quantity comparison
    total_quantity_po = Column(Numeric(15, 4), nullable=True)
    total_quantity_invoice = Column(Numeric(15, 4), nullable=True)
    total_quantity_dn = Column(Numeric(15, 4), nullable=True)
    quantity_variance = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    
    # Match status
    match_status = Column(String(50), default="pending", nullable=False)  # confirmed, pending, rejected
    decision = Column(String(50), nullable=False)  # AUTO_APPROVE, HUMAN_REVIEW, DISPUTE
    
    # Match type
    match_type = Column(String(50), nullable=False)  # full, partial, cross_match
    
    # Amount breakdown
    auto_approved_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    pending_review_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    disputed_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Resolution
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Layer info
    layer = Column(Integer, default=1, nullable=False)  # 1=Anchor, 2=Cascade, 3=Balance
    match_sequence = Column(Integer, default=1, nullable=False)
    
    # Metadata
    matched_by = Column(String(36), nullable=True)
    confirmed_by = Column(String(36), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Timestamps for matching
    po_date = Column(Date, nullable=True)
    invoice_date = Column(Date, nullable=True)
    dn_date = Column(Date, nullable=True)
    
    # Variances found
    has_amount_variance = Column(Boolean, default=False, nullable=False)
    has_quantity_variance = Column(Boolean, default=False, nullable=False)
    has_date_variance = Column(Boolean, default=False, nullable=False)
    has_price_variance = Column(Boolean, default=False, nullable=False)

    # Relationships
    lines: List["MatchResultLine"] = relationship(
        "MatchResultLine",
        back_populates="match_result",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Optional["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="match_results",
    )
    invoice: Optional["Invoice"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="match_results",
    )
    delivery_note: Optional["DeliveryNote"] = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="match_results",
    )

    def __repr__(self) -> str:
        return f"<MatchResult {self.id} - {self.match_status}>"

    @property
    def is_auto_approvable(self) -> bool:
        """Check if this match can be auto-approved."""
        return self.decision == "AUTO_APPROVE" and not self.resolved

    @property
    def needs_human_review(self) -> bool:
        """Check if this match needs human review."""
        return self.decision == "HUMAN_REVIEW" and not self.resolved


class MatchResultLine(Base, BaseModel):
    """Match Result Line - line-level matching details."""
    __tablename__ = "match_result_lines"

    match_result_id = Column(
        String(36),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line references
    po_line_id = Column(String(36), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    invoice_line_id = Column(String(36), ForeignKey("invoice_lines.id", ondelete="SET NULL"), nullable=True)
    dn_line_id = Column(String(36), ForeignKey("delivery_note_lines.id", ondelete="SET NULL"), nullable=True)
    
    # Line scores
    match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    
    # Quantities
    po_quantity = Column(Numeric(15, 4), nullable=True)
    invoice_quantity = Column(Numeric(15, 4), nullable=True)
    dn_quantity = Column(Numeric(15, 4), nullable=True)
    matched_quantity = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    variance_quantity = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    
    # Amounts
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Prices
    po_unit_price = Column(Numeric(15, 4), nullable=True)
    invoice_unit_price = Column(Numeric(15, 4), nullable=True)
    dn_unit_price = Column(Numeric(15, 4), nullable=True)
    price_variance = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    price_variance_percent = Column(Numeric(8, 4), default=Decimal("0.0000"), nullable=False)
    
    # Item info
    item_code = Column(String(50), nullable=True)
    item_description = Column(String(500), nullable=True)
    
    # Status
    match_status = Column(String(50), default="matched", nullable=False)  # matched, variance, unmatched
    
    # Relationships
    match_result: "MatchResult" = relationship(
        "MatchResult",
        back_populates="lines",
    )
    po_line: Optional["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    invoice_line: Optional["InvoiceLine"] = relationship(
        "InvoiceLine",
        foreign_keys=[invoice_line_id],
    )
    dn_line: Optional["DeliveryNoteLine"] = relationship(
        "DeliveryNoteLine",
        foreign_keys=[dn_line_id],
    )

    def __repr__(self) -> str:
        return f"<MatchResultLine {self.item_code}>"
