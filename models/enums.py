# models/enums.py
"""Status enums and decision types for the matching engine."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status enum."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status enum."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status enum."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching engine decision types."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"
    NO_MATCH = "no_match"


class ExceptionType(str, Enum):
    """Exception types for matching failures."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_MISMATCH = "date_mismatch"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH_FOUND = "no_match_found"
    TOLERANCE_EXCEEDED = "tolerance_exceeded"


class MatchConfidence(str, Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
