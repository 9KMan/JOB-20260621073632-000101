// models/enums.py
"""Enumeration types for AP Automation Engine.

Defines status enums, decision types, and other categorical
values used throughout the application.
"""

import uuid
from enum import Enum

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator


class UUIDType(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """

    impl = UUID(as_uuid=True) if False else String(36)  # noqa: SIM108
    cache_ok = True

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: Any) -> str | None:
        """Convert UUID to string for database binding."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> uuid.UUID | None:
        """Convert string from database to UUID."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class InvoiceStatus(str, Enum):
    """Invoice status lifecycle."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
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


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class MatchingDecision(str, Enum):
    """Matching engine decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PENDING = "pending"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    DATE_VARIANCE = "date_variance"
    TAX_MISMATCH = "tax_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"
    OTHER = "other"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CNY = "CNY"
    HKD = "HKD"
    SGD = "SGD"


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
