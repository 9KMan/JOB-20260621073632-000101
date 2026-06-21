// src/models/document.py
"""Document models for Invoice, Purchase Order, and Delivery Note."""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.database import Base


class DocumentType(str, enum.Enum):
    """Document type enumeration."""

    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    DELIVERY_NOTE = "delivery_note"


class DocumentStatus(str, enum.Enum):
    """Document status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    CONFIRMED = "confirmed"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Document(Base):
    """Base document model with common fields."""

    __tablename__ = "documents"
    __mapper_args__ = {"polymorphic_on": "doc_type", "polymorphic_identity": "document"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doc_type = Column(String(50), nullable=False, index=True)
    doc_number = Column(String(100), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_code = Column(String(50), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    po_number = Column(String(100), ForeignKey("purchase_orders.po_number"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default=DocumentStatus.PENDING.value, index=True)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    matched_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    balance_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    issue_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    received_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="documents")
    lines = relationship("DocumentLine", back_populates="document", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="document", cascade="all, delete-orphan")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_documents")
    confirmed_by_user = relationship("User", foreign_keys=[confirmed_by], back_populates="confirmed_documents")

    __table_args__ = (
        Index("ix_documents_supplier_doc_number", "supplier_id", "doc_number", unique=True),
        Index("ix_documents_po_number", "po_number"),
        Index("ix_documents_status_date", "status", "issue_date"),
    )


class Invoice(Base):
    """Invoice document model."""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    po_number = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default=DocumentStatus.PENDING.value)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    balance_amount = Column(Numeric(15, 2), nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    received_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Polymorphic relationship
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    document = relationship("Document", foreign_keys=[document_id])

    __table_args__ = (
        Index("ix_invoices_supplier_date", "supplier_id", "issue_date"),
    )


class PurchaseOrder(Base):
    """Purchase Order document model."""

    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), nullable=False, unique=True, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    supplier_code = Column(String(50), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default=DocumentStatus.DRAFT.value)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    balance_amount = Column(Numeric(15, 2), nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Polymorphic relationship
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    document = relationship("Document", foreign_keys=[document_id])

    # Relationships
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order", foreign_keys="Invoice.po_number", primaryjoin="PurchaseOrder.po_number==Invoice.po_number")
    delivery_notes = relationship("DeliveryNote", back_populates="purchase_order")

    __table_args__ = (
        Index("ix_purchase_orders_supplier_status", "supplier_id", "status"),
    )


class DeliveryNote(Base):
    """Delivery Note document model."""

    __tablename__ = "delivery_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dn_number = Column(String(100), nullable=False, unique=True, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    po_number = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default=DocumentStatus.PENDING.value)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    balance_amount = Column(Numeric(15, 2), nullable=False)
    issue_date = Column(Date, nullable=False)
    received_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    carrier = Column(String(255), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Polymorphic relationship
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    document = relationship("Document", foreign_keys=[document_id])

    # Relationships
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_number], primaryjoin="DeliveryNote.po_number==PurchaseOrder.po_number", back_populates="delivery_notes")
    lines = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_delivery_notes_supplier_date", "supplier_id", "issue_date"),
    )


# Additional models for detailed line items

class DocumentLine(Base):
    """Base document line model."""

    __tablename__ = "document_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    document_type = Column(String(50), nullable=False)
    line_number = Column(String(50), nullable=False)
    product_code = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), nullable=False, default="EA")
    unit_price = Column(Numeric(15, 4), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False)
    matched_quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0.00"))
    balance_quantity = Column(Numeric(15, 3), nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="lines")

    __table_args__ = (
        Index("ix_document_lines_document_line", "document_id", "line_number", unique=True),
        Index("ix_document_lines_product", "product_code"),
    )


class PurchaseOrderLine(Base):
    """Purchase order line item model."""

    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    line_number = Column(String(50), nullable=False)
    product_code = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), nullable=False, default="EA")
    unit_price = Column(Numeric(15, 4), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False)
    delivered_quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0.00"))
    invoiced_quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0.00"))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    __table_args__ = (
        Index("ix_po_lines_order_line", "purchase_order_id", "line_number", unique=True),
    )


class DeliveryNoteLine(Base):
    """Delivery note line item model."""

    __tablename__ = "delivery_note_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id"), nullable=False)
    line_number = Column(String(50), nullable=False)
    product_code = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), nullable=False, default="EA")
    unit_price = Column(Numeric(15, 4), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")

    __table_args__ = (
        Index("ix_dn_lines_note_line", "delivery_note_id", "line_number", unique=True),
    )


class Supplier(Base):
    """Supplier model."""

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_code = Column(String(50), nullable=False, unique=True, index=True)
    supplier_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    tax_id = Column(String(50), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="supplier")
    invoices = relationship("Invoice", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    delivery_notes = relationship("DeliveryNote", back_populates="supplier")
