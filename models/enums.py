# models/enums.py
"""
Enum definitions for the AP Automation system.

Defines status enums, decision types, and other enumerated
values used throughout the application.
"""

import uuid
from enum import Enum

from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class InvoiceStatus(str, Enum):
    """Invoice processing status."""

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    PENDING = "pending"


class MatchConfidence(str, Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_INVOICE = "missing_invoice"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DUPLICATE_PO = "duplicate_po"
    DATE_VARIANCE = "date_variance"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH = "no_match"
    PARTIAL_MATCH = "partial_match"
    BLOCKED = "blocked"
    OTHER = "other"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LedgerEntryType(str, Enum):
    """Types of ledger entries."""

    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    CREDIT_MEMO = "credit_memo"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"


class MatchPairType(str, Enum):
    """Types of matched document pairs."""

    PO_INVOICE = "po_invoice"
    PO_DELIVERY_INVOICE = "po_delivery_invoice"
    INVOICE_ONLY = "invoice_only"


class UUIDType(TypeDecorator):
    """
    Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available,
    otherwise stores as String(36).
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeDecorator:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect) -> str | None:
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect) -> uuid.UUID | None:
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)
