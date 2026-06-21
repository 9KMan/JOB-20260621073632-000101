// src/models/models.py
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Integer,
    Enum as SQLEnum,
    Text,
    Boolean,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.app.database import Base


class DocumentStatus(str):
    """Document status options."""
    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class MatchStatus(str):
    """Match status options."""
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class MatchType(str):
    """Type of match performed."""
    PO_INVOICE = "po_invoice"
    PO_DELIVERY = "po_delivery"
    INVOICE_DELIVERY = "invoice_delivery"
    THREE_WAY = "three_way"


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Supplier(BaseModel):
    """Supplier/Vendor model."""
    __tablename__ = "suppliers"
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="supplier"
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="supplier"
    )
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote", back_populates="supplier"
    )
    
    def __repr__(self) -> str:
        return f"<Supplier(code={self.code}, name={self.name})>"


class PurchaseOrder(BaseModel):
    """Purchase Order model."""
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=DocumentStatus.DRAFT, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_invoices: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        foreign_keys="MatchRecord.po_id",
        back_populates="purchase_order",
    )
    
    __table_args__ = (
        Index("ix_po_supplier_status", "supplier_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(po_number={self.po_number}, total={self.total_amount})>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item model."""
    __tablename__ = "purchase_order_lines"
    
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    
    __table_args__ = (
        UniqueConstraint("po_id", "line_number", name="uq_po_line"),
    )
    
    def __repr__(self) -> str:
        return f"<POLine(po={self.po_id}, line={self.line_number}, amount={self.line_amount})>"


class Invoice(BaseModel):
    """Invoice model."""
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    po_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    invoice_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=DocumentStatus.DRAFT, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="invoices")
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matched_pos: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        foreign_keys="MatchRecord.invoice_id",
        back_populates="invoice",
    )
    
    __table_args__ = (
        Index("ix_invoice_supplier_status", "supplier_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(number={self.invoice_number}, amount={self.total_amount})>"


class InvoiceLine(BaseModel):
    """Invoice Line Item model."""
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    
    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line"),
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(invoice={self.invoice_id}, line={self.line_number})>"


class DeliveryNote(BaseModel):
    """Delivery Note / Goods Received Note model."""
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    po_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    delivery_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    received_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=DocumentStatus.DRAFT, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="delivery_notes")
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    matched_pos: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        foreign_keys="MatchRecord.dn_id",
        back_populates="delivery_note",
    )
    
    __table_args__ = (
        Index("ix_dn_supplier_status", "supplier_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(number={self.dn_number}, amount={self.total_amount})>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line Item model."""
    __tablename__ = "delivery_note_lines"
    
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity_delivered: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_accepted: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_rejected: Mapped[float] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    
    __table_args__ = (
        UniqueConstraint("dn_id", "line_number", name="uq_dn_line"),
    )
    
    def __repr__(self) -> str:
        return f"<DNLine(dn={self.dn_id}, line={self.line_number}, qty={self.quantity_delivered})>"


class MatchRecord(BaseModel):
    """Match Record - stores all document matches."""
    __tablename__ = "match_records"
    
    # Document references (at least one pair must be set)
    po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True
    )
    dn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=True
    )
    
    # Match details
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=MatchStatus.PENDING, nullable=False, index=True
    )
    
    # Scoring
    line_level_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    amount_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    date_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    total_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    
    # Amount comparison
    po_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    invoice_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    dn_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Matched line details (JSON for flexibility)
    matched_lines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    
    # Decision
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Human review
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder", foreign_keys=[po_id], back_populates="matched_invoices"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice", foreign_keys=[invoice_id], back_populates="matched_pos"
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote", foreign_keys=[dn_id], back_populates="matched_pos"
    )
    balance_records: Mapped[List["BalanceRecord"]] = relationship(
        "BalanceRecord", back_populates="match_record", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_match_status_type", "status", "match_type"),
        Index("ix_match_documents", "po_id", "invoice_id", "dn_id"),
    )
    
    def __repr__(self) -> str:
        return f"<MatchRecord(id={self.id}, type={self.match_type}, score={self.total_score})>"


class BalanceRecord(BaseModel):
    """Balance Ledger - tracks partial matches and balances."""
    __tablename__ = "balance_records"
    
    match_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_records.id", ondelete="CASCADE"), nullable=False
    )
    
    # Document type this balance applies to
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PO, Invoice, DN
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    # Balance tracking
    original_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    balance_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Resolution status
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by_match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    match_record: Mapped["MatchRecord"] = relationship(
        "MatchRecord", back_populates="balance_records"
    )
    
    __table_args__ = (
        Index("ix_balance_doc", "document_type", "document_id"),
        Index("ix_balance_unresolved", "is_resolved", "balance_amount"),
    )
    
    def __repr__(self) -> str:
        return f"<BalanceRecord(doc={self.document_type}, balance={self.balance_amount})>"


class User(BaseModel):
    """User model for authentication and approval."""
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="reviewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Approval limits
    approval_limit: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    def __repr__(self) -> str:
        return f"<User(email={self.email}, role={self.role})>"
