// src/models/document.py
"""Document models for Purchase Orders, Invoices, and Delivery Notes."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class DocumentType(str, Enum):
    """Document type enumeration."""
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Document(Base):
    """Base document model with common fields."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType, name="document_type_enum"),
        nullable=False,
        index=True,
    )
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Financial fields
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    # Dates
    document_date: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        Date,
        nullable=True,
    )
    delivery_date: Mapped[Optional[datetime]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Status and matching
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus, name="document_status_enum"),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    match_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    matched_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Audit fields
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    # Relationships
    created_by_user = relationship(
        "User",
        back_populates="created_documents",
        foreign_keys=[created_by],
    )
    line_items = relationship(
        "DocumentLineItem",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    matched_document = relationship(
        "Document",
        remote_side=[id],
        foreign_keys=[matched_document_id],
    )

    __table_args__ = (
        Index("ix_documents_supplier_date", "supplier_id", "document_date"),
        Index("ix_documents_type_status", "document_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Document {self.document_type.value}:{self.document_number}>"

    def to_dict(self) -> dict:
        """Convert document to dictionary."""
        return {
            "id": str(self.id),
            "document_type": self.document_type.value,
            "document_number": self.document_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "total_amount": str(self.total_amount),
            "tax_amount": str(self.tax_amount),
            "currency": self.currency,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "status": self.status.value,
            "matched_amount": str(self.matched_amount),
            "match_score": self.match_score,
            "metadata": self.metadata,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DocumentLineItem(Base):
    """Line items for documents."""

    __tablename__ = "document_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    expected_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    delivered_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    invoiced_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
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

    # Relationships
    document = relationship("Document", back_populates="line_items")

    def __repr__(self) -> str:
        return f"<LineItem {self.line_number}:{self.product_code}>"

    def to_dict(self) -> dict:
        """Convert line item to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "line_number": self.line_number,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "description": self.description,
            "quantity": str(self.quantity),
            "unit_of_measure": self.unit_of_measure,
            "unit_price": str(self.unit_price),
            "line_total": str(self.line_total),
            "tax_rate": str(self.tax_rate),
            "expected_quantity": str(self.expected_quantity) if self.expected_quantity else None,
            "delivered_quantity": str(self.delivered_quantity) if self.delivered_quantity else None,
            "invoiced_quantity": str(self.invoiced_quantity) if self.invoiced_quantity else None,
        }


# Alias models for backwards compatibility
PurchaseOrder = Document
Invoice = Document
DeliveryNote = Document
