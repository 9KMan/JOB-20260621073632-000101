// src/models/models.py
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, 
    Integer, Text, Enum, Boolean, Index, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.app.database import Base


class MatchStatus(str, PyEnum):
    """Match status enumeration."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class MatchDecision(str, PyEnum):
    """Match decision enumeration."""
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")


class Vendor(Base):
    """Vendor/Supplier model."""
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    tax_id = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")
    delivery_notes = relationship("DeliveryNote", back_populates="vendor")

    __table_args__ = (
        Index("ix_vendors_vendor_code_name", "vendor_code", "name"),
    )


class PurchaseOrder(Base):
    """Purchase Order model."""
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    order_date = Column(DateTime, nullable=False)
    expected_delivery_date = Column(DateTime)
    status = Column(String(50), default="OPEN")
    currency = Column(String(3), default="USD")
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")
    delivery_notes = relationship("DeliveryNote", back_populates="purchase_order")
    match_results = relationship("MatchResult", back_populates="purchase_order")

    __table_args__ = (
        Index("ix_po_vendor_date", "vendor_id", "order_date"),
        Index("ix_po_po_number", "po_number"),
    )


class PurchaseOrderLine(Base):
    """Purchase Order Line Item model."""
    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100))
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA")
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    __table_args__ = (
        Index("ix_pol_po_line", "purchase_order_id", "line_number"),
    )


class Invoice(Base):
    """Invoice model."""
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    status = Column(String(50), default="RECEIVED")
    currency = Column(String(3), default="USD")
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="invoice")

    __table_args__ = (
        Index("ix_invoice_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoice_po", "purchase_order_id"),
    )


class InvoiceLine(Base):
    """Invoice Line Item model."""
    __tablename__ = "invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100))
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA")
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")
    po_line = relationship("PurchaseOrderLine")

    __table_args__ = (
        Index("ix_il_invoice_line", "invoice_id", "line_number"),
    )


class DeliveryNote(Base):
    """Delivery Note / Goods Receipt model."""
    __tablename__ = "delivery_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dn_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    delivery_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="RECEIVED")
    currency = Column(String(3), default="USD")
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="delivery_notes")
    purchase_order = relationship("PurchaseOrder", back_populates="delivery_notes")
    lines = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="delivery_note")

    __table_args__ = (
        Index("ix_dn_vendor_date", "vendor_id", "delivery_date"),
        Index("ix_dn_po", "purchase_order_id"),
    )


class DeliveryNoteLine(Base):
    """Delivery Note Line Item model."""
    __tablename__ = "delivery_note_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100))
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA")
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    po_line = relationship("PurchaseOrderLine")

    __table_args__ = (
        Index("ix_dnl_dn_line", "delivery_note_id", "line_number"),
    )


class MatchResult(Base):
    """Match Result model for storing matching outcomes."""
    __tablename__ = "match_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    
    match_type = Column(String(50), nullable=False)  # 'INVOICE_PO', 'DN_PO', 'INVOICE_DN', '3_WAY'
    match_status = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    match_decision = Column(Enum(MatchDecision), nullable=True)
    
    total_score = Column(Float, nullable=False)
    line_score = Column(Float, default=0)
    amount_score = Column(Float, default=0)
    date_score = Column(Float, default=0)
    
    amount_difference = Column(Numeric(15, 2), default=0)
    quantity_difference = Column(Numeric(15, 4), default=0)
    
    notes = Column(Text)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="match_results")
    delivery_note = relationship("DeliveryNote", back_populates="match_results")
    purchase_order = relationship("PurchaseOrder", back_populates="match_results")
    decision_user = relationship("User")
    scores = relationship("MatchScore", back_populates="match_result", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_mr_invoice", "invoice_id"),
        Index("ix_mr_delivery_note", "delivery_note_id"),
        Index("ix_mr_purchase_order", "purchase_order_id"),
        Index("ix_mr_status", "match_status"),
    )


class MatchScore(Base):
    """Detailed match scores for line-level matching."""
    __tablename__ = "match_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_result_id = Column(UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE"), nullable=False)
    
    invoice_line_id = Column(UUID(as_uuid=True), ForeignKey("invoice_lines.id", ondelete="SET NULL"), nullable=True)
    delivery_note_line_id = Column(UUID(as_uuid=True), ForeignKey("delivery_note_lines.id", ondelete="SET NULL"), nullable=True)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    
    score = Column(Float, nullable=False)
    quantity_match_score = Column(Float, default=0)
    price_match_score = Column(Float, default=0)
    description_match_score = Column(Float, default=0)
    
    quantity_difference = Column(Numeric(15, 4), default=0)
    price_difference = Column(Numeric(15, 4), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    match_result = relationship("MatchResult", back_populates="scores")


class BalanceLedger(Base):
    """Balance Ledger for tracking partial matches and balances."""
    __tablename__ = "balance_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    document_type = Column(String(20), nullable=False)  # 'PO', 'INVOICE', 'DN'
    document_id = Column(UUID(as_uuid=True), nullable=False)
    document_line_id = Column(UUID(as_uuid=True), nullable=True)
    
    balance_type = Column(String(20), nullable=False)  # 'OPEN', 'INVOICED', 'DELIVERED', 'PAID'
    amount = Column(Numeric(15, 2), nullable=False)
    
    related_document_type = Column(String(20), nullable=True)
    related_document_id = Column(UUID(as_uuid=True), nullable=True)
    
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_bl_doc", "document_type", "document_id"),
        Index("ix_bl_balance_type", "balance_type"),
    )


class AuditLog(Base):
    """Audit log for tracking all changes."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    old_values = Column(Text, nullable=True)  # JSON string
    new_values = Column(Text, nullable=True)  # JSON string
    
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_al_entity", "entity_type", "entity_id"),
        Index("ix_al_user", "user_id"),
        Index("ix_al_created", "created_at"),
    )
