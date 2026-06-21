// src/models/match.py
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
import enum
from src.models.base import BaseModel


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class MatchDecision(str, enum.Enum):
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    DISPUTE = "dispute"


class Match(BaseModel):
    __tablename__ = "matches"
    
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    
    match_type = Column(String(50), nullable=False)  # "invoice_po", "dn_po", "invoice_dn", "three_way"
    match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.PENDING, nullable=False)
    decision = Column(SQLEnum(MatchDecision), nullable=True)
    
    invoice_amount = Column(Numeric(15, 2), nullable=False)
    po_amount = Column(Numeric(15, 2), nullable=False)
    variance_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    confirmed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('invoice_id', 'purchase_order_id', name='uix_invoice_po'),
        UniqueConstraint('invoice_id', 'delivery_note_id', name='uix_invoice_dn'),
    )
    
    invoice = relationship("Invoice", back_populates="matches")
    delivery_note = relationship("DeliveryNote", back_populates="matches")
    purchase_order = relationship("PurchaseOrder", back_populates="matches")
    lines = relationship("MatchLine", back_populates="match", cascade="all, delete-orphan")


class MatchLine(BaseModel):
    __tablename__ = "match_lines"
    
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    
    invoice_line_id = Column(UUID(as_uuid=True), ForeignKey("invoice_lines.id", ondelete="CASCADE"), nullable=True)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="CASCADE"), nullable=True)
    dn_line_id = Column(UUID(as_uuid=True), ForeignKey("delivery_note_lines.id", ondelete="CASCADE"), nullable=True)
    
    product_code = Column(String(50), nullable=False)
    invoice_quantity = Column(Numeric(15, 4), nullable=True)
    po_quantity = Column(Numeric(15, 4), nullable=True)
    dn_quantity = Column(Numeric(15, 4), nullable=True)
    
    line_match_score = Column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    quantity_variance = Column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    
    match = relationship("Match", back_populates="lines")
