// src/models/document.py
"""Document models for PO, Invoice, and Delivery Note."""
import decimal
import enum
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class DocumentType(str, enum.Enum):
    """Document type enumeration."""

    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"


class DocumentStatus(str, enum.Enum):
    """Document status enumeration."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHED = "matched"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Document(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Main document model representing PO, Invoice, or Delivery Note.
    Acts as the anchor for 3-way matching.
    """

    __tablename__ = "documents"

    # Document identification
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        nullable=False,
        index=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Supplier information
    supplier_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    supplier_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Dates
    document_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial amounts
    subtotal: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Linkage for PO anchoring
    linked_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    linked_po: Mapped[Optional["Document"]] = relationship(
        "Document",
        remote_side="Document.id",
        foreign_keys=[linked_po_id],
        back_populates="linked_documents",
    )
    linked_documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="linked_po",
        foreign_keys="Document.linked_po_id",
    )

    # Matching metadata
    is_fully_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    remaining_balance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )

    # Additional info
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        nullable=True,
    )

    # Lines relationship
    lines: Mapped[list["DocumentLine"]] = relationship(
        "DocumentLine",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Matching records relationship
    matching_records: Mapped[list["MatchingRecord"]] = relationship(
        "MatchingRecord",
        back_populates="document",
        foreign_keys="MatchingRecord.document_id",
    )

    # Balance records relationship
    balance_records: Mapped[list["BalanceRecord"]] = relationship(
        "BalanceRecord",
        back_populates="document",
    )

    __table_args__ = (
        Index("ix_documents_type_status", "document_type", "status"),
        Index("ix_documents_supplier_date", "supplier_code", "document_date"),
        Index("ix_documents_type_number", "document_type", "document_number"),
    )

    def __repr__(self) -> str:
        return f"<Document {self.document_type.value}:{self.document_number}>"


# Import at bottom to avoid circular imports
from src.models.matching import BalanceRecord, MatchingRecord


class DocumentLine(Base, UUIDMixin, TimestampMixin):
    """
    Individual line items within a document.
    Used for line-level matching between documents.
    """

    __tablename__ = "document_lines"

    # Parent document
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="lines",
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    external_line_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Product/Service information
    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    item_description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )
    quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Pricing
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )
    line_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    tax_rate: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )

    # Matching
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0"),
        nullable=False,
    )

    # Linkage
    linked_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index("ix_document_lines_document", "document_id", "line_number"),
        Index("ix_document_lines_item", "item_code"),
    )

    def __repr__(self) -> str:
        return f"<DocumentLine {self.line_number}:{self.item_code}>"


# Import at bottom to avoid circular import issues
from datetime import date
from src.models.matching import MatchingRecord, BalanceRecord
