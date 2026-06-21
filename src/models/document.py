// src/models/document.py
"""Base document model for PO, Invoice, and Delivery Note."""
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.document_line import DocumentLine
    from src.models.user import User


class DocumentType(str, Enum):
    """Types of documents in the system."""
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"


class DocumentStatus(str, Enum):
    """Status of a document."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    DISPUTED = "disputed"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Document(UUIDMixin, TimestampMixin, Base):
    """
    Base document model representing PO, Invoice, or Delivery Note.
    Uses single-table inheritance pattern for different document types.
    """
    
    __tablename__ = "documents"
    __mapper_args__ = {
        "polymorphic_identity": "document",
        "polymorphic_on": "document_type",
    }
    
    # Document identification
    document_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType, name="document_type_enum"),
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus, name="document_status_enum"),
        default=DocumentStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    
    # Supplier information
    supplier_code: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Reference numbers
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Dates
    document_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    expected_delivery_date: Mapped[Optional[Date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Financial
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Audit
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    lines: Mapped[list["DocumentLine"]] = relationship(
        "DocumentLine",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    
    def __repr__(self) -> str:
        return f"<Document {self.document_type.value}:{self.document_number}>"
    
    @property
    def is_po(self) -> bool:
        """Check if this is a purchase order."""
        return self.document_type == DocumentType.PURCHASE_ORDER
    
    @property
    def is_invoice(self) -> bool:
        """Check if this is an invoice."""
        return self.document_type == DocumentType.INVOICE
    
    @property
    def is_delivery_note(self) -> bool:
        """Check if this is a delivery note."""
        return self.document_type == DocumentType.DELIVERY_NOTE
    
    @property
    def open_amount(self) -> Decimal:
        """Calculate open (unmatched) amount."""
        from src.models.balance import Balance, BalanceType
        matched_amount = sum(
            b.amount for b in self.balances 
            if b.balance_type == BalanceType.DEBIT if self.is_po or self.is_delivery_note
            else b.amount if b.balance_type == BalanceType.CREDIT else Decimal("0")
            for b in self.balances
        )
        return self.total_amount - matched_amount


import uuid
