# src/models/match_line_item.py
"""Match Line Item model for detailed line-level matching."""
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin


class MatchLineItem(Base, UUIDMixin, TimestampMixin):
    """Match Line Item model for detailed line-level matching."""
    
    __tablename__ = "match_line_items"
    
    match_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # PO Line Item reference
    po_line_item_id = Column(UUID(as_uuid=True), nullable=True)
    po_line_number = Column(String(10), nullable=True)
    po_sku = Column(String(100), nullable=True)
    
    # Invoice Line Item reference
    invoice_line_item_id = Column(UUID(as_uuid=True), nullable=True)
    invoice_line_number = Column(String(10), nullable=True)
    invoice_sku = Column(String(100), nullable=True)
    
    # Delivery Note Line Item reference
    dn_line_item_id = Column(UUID(as_uuid=True), nullable=True)
    dn_line_number = Column(String(10), nullable=True)
    dn_sku = Column(String(100), nullable=True)
    
    # Matched quantities
    po_quantity = Column(Numeric(15, 3), nullable=True)
    invoice_quantity = Column(Numeric(15, 3), nullable=True)
    dn_quantity = Column(Numeric(15, 3), nullable=True)
    
    # Matched amounts
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    
    # Match status
    is_matched = Column(String(1), default="N", nullable=False)
    match_type = Column(String(20), nullable=True)
    
    # Variance
    quantity_variance = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    amount_variance = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    variance_percentage = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    
    # Match details as JSON
    match_data = Column(JSON, nullable=True)
    
    # Relationships
    match_result = relationship("MatchResult", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<MatchLineItem(id={self.id}, po_sku={self.po_sku}, invoice_sku={self.invoice_sku})>"
