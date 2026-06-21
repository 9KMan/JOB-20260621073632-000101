// src/models/document.py
"""Document models for invoices, delivery notes, and purchase orders."""
import enum
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Index, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class DocumentType(str, enum.Enum):
    """Document type enumeration."""
    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class DocumentStatus(str, enum.Enum):
    """Document status enumeration."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MATCHED = "MATCHED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Document(BaseModel):
    """Main document model (Invoice, Delivery Note, or Purchase Order)."""
    __tablename__ = "documents"

    document_type: Mapped[str] = mapped_column(
        Enum(DocumentType),
        nullable=False,
        index=True
    )
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    document_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=DocumentStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    lines: Mapped[list["DocumentLine"]] = relationship(
        "DocumentLine",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("ix_documents_supplier_date", "supplier_id", "document_date"),
        Index("ix_documents_type_status", "document_type", "status"),
    )


class DocumentLine(BaseModel):
    """Line items within a document."""
    __tablename__ = "document_lines"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False
    )
    item_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    uom: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    tax_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="lines"
    )

    __table_args__ = (
        Index("ix_document_lines_document_line", "document_id", "line_number"),
    )
