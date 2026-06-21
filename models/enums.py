# models/enums.py
"""Enum definitions for status and decision types.

All enums are PostgreSQL-compatible for efficient database storage.
"""

import uuid
from enum import Enum

from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID


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
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIALLY_RECEIVED = "partially_received"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class MatchingStatus(str, Enum):
    """Matching process status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_MATCH = "no_match"


class DecisionType(str, Enum):
    """Matching decision type."""

    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"


class ExceptionType(str, Enum):
    """Exception classification types."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH = "no_match"
    OTHER = "other"


class MatchConfidence(str, Enum):
    """Match confidence level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class LearningStatus(str, Enum):
    """Learning loop status for cross-references."""

    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"


class BalanceType(str, Enum):
    """Balance ledger entry type."""

    INVOICE = "invoice"
    CREDIT_MEMO = "credit_memo"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"


class MatchSource(str, Enum):
    """Source of match confirmation."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    LEARNING = "learning"
    USER_APPROVED = "user_approved"


class UUIDType(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as String(36).
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeDecorator:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: uuid.UUID | str | None, dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value: str | None, dialect) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)
